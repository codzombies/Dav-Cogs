import logging

import discord
from redbot.core import checks, commands
from redbot.core.i18n import Translator, cog_i18n

_ = Translator("Check", __file__)


@cog_i18n(_)
class Check(commands.Cog):
    """Check"""

    __version__ = "2.1.0-dev1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        # Thanks Sinbad! And Trusty in whose cogs I found this.
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nVersion: {self.__version__}"

    async def red_delete_data_for_user(self, *, requester, user_id):
        # This cog stores no EUD
        return

    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger("red.cog.dav-cogs.check")

    @commands.command()
    @commands.guild_only()
    @checks.mod()
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def check(self, ctx, member: discord.Member):
        ctx.assume_yes = True
        async with ctx.typing():
            await ctx.send(
                _(":mag_right: Starting lookup for: {usermention}({userid})").format(
                    usermention=member.mention, userid=member.id
                )
            )
            await self._userinfo(ctx, member)
            await self._maybe_altmarker(ctx, member)
            await self._warnings_or_read(ctx, member)
            await self._maybe_listflag(ctx, member)
    async def listcases(
        self,
        ctx: commands.Context,
        per_embed: Optional[commands.Range[int, 1, 19]] = 6,
        *,
        member: Union[discord.Member, int],
    ):
        """List cases for the specified member."""
        async with ctx.typing():
            try:
                if isinstance(member, int):
                    cases = await get_cases_for_member(
                        bot=ctx.bot, guild=ctx.guild, member_id=member
                    )
                else:
                    cases = await get_cases_for_member(bot=ctx.bot, guild=ctx.guild, member=member)
            except discord.NotFound:
                return await ctx.send("That user does not exist.")
            except discord.HTTPException:
                return await ctx.send(
                    "Something unexpected went wrong while fetching that user by ID."
                )
            if not cases:
                return await ctx.send("That user does not have any cases.")

            rendered_cases = []
            for page, ccases in enumerate(chunks(cases, per_embed), 1):
                embed = discord.Embed(
                    title=f"Cases for `{getattr(member, 'display_name', member)}` (Page {page} / {len(cases) // per_embed + 1 if len(cases) % per_embed else len(cases) // per_embed})",
                )
                for case in ccases:
                    if case.moderator is None:
                        moderator = "Unknown"
                    elif isinstance(case.moderator, int):
                        if case.moderator == 0xDE1:
                            moderator = "Deleted User."
                        else:
                            translated = "Unknown or Deleted User"
                            moderator = f"[{translated}] ({case.moderator})"
                    else:
                        moderator = f"{case.moderator} ({case.moderator.id})"

                    length = ""
                    if case.until:
                        start = datetime.fromtimestamp(case.created_at, tz=timezone.utc)
                        end = datetime.fromtimestamp(case.until, tz=timezone.utc)
                        end_fmt = discord.utils.format_dt(end)
                        duration = end - start
                        dur_fmt = cf.humanize_timedelta(timedelta=duration)
                        until = f"Until: {end_fmt}\n"
                        duration = f"Length: {dur_fmt}\n"
                        length = until + duration

                    created_at = datetime.fromtimestamp(case.created_at, tz=timezone.utc)
                    embed.add_field(
                        name=f"Case #{case.case_number} | {(await get_casetype(case.action_type, getattr(member, 'guild', ctx.guild))).case_str}",
                        value=f"{cf.bold('Moderator:')} {moderator}\n"
                        f"{cf.bold('Reason:')} {case.reason}\n"
                        f"{length}"
                        f"{cf.bold('Timestamp:')} {discord.utils.format_dt(created_at)}\n\n",
                        inline=False,
                    )
                rendered_cases.append(embed)

        await menu(ctx, rendered_cases)
        await ctx.send(_("Lookup completed."))

    async def _userinfo(self, ctx, member):
        try:
            await ctx.invoke(ctx.bot.get_command("userinfo"), member=member)
        except TypeError:
            try:
                await ctx.invoke(ctx.bot.get_command("userinfo"), user=member)
            except:
                pass
        except Exception as e:
            self.log.exception(f"Error in userinfo {e}", exc_info=True)

    async def _warnings_or_read(self, ctx, member):
        try:
            await ctx.invoke(ctx.bot.get_command("read"), member=member.id)
        except:
            try:
                await ctx.invoke(ctx.bot.get_command("warnings"), member=member.id)
            except:
                self.log.debug("Command warn not found.")

    async def _maybe_listflag(self, ctx, member):
        try:
            await ctx.invoke(ctx.bot.get_command("listflag"), member=member)
        except:
            self.log.debug("Command listflag not found.")

    async def _maybe_altmarker(self, ctx, member):
        try:
            await ctx.invoke(ctx.bot.get_command("alt get"), member=member)
        except:
            self.log.debug("Altmarker not found.")
