"""The `reposcout` command-line app: wires auth, cache, GitHub, bucketing, and output together."""

from __future__ import annotations

from pathlib import Path

import typer

from reposcout import auth, bucketing, cache, github, output

app = typer.Typer(help="Search GitHub for repos by keyword, ranked and classified by activity.")


@app.callback()
def _main() -> None:
    """reposcout: search GitHub for repos by keyword, ranked and activity-bucketed."""


@app.command()
def search(
    keyword: str = typer.Argument(..., help='Search keyword, e.g. "expense tracker"'),
    refresh: bool = typer.Option(
        False, "--refresh", help="Bypass the cache and fetch fresh results from GitHub."
    ),
) -> None:
    """Search GitHub repos by keyword and print a ranked, activity-bucketed report."""
    token = auth.resolve_token()

    if not refresh:
        cached = cache.read_cache(keyword)
        if cached is not None:
            _emit_results(keyword, cached.total_count, cached.repos)
            return

    try:
        result = github.search_repositories(keyword, token)
    except github.InvalidTokenError:
        if token is None:
            typer.echo("GitHub rejected the request as unauthorized.")
            raise typer.Exit(code=1)
        new_token = auth.handle_invalid_token()
        try:
            result = github.search_repositories(keyword, new_token)
        except github.RateLimitExceeded as exc:
            typer.echo(auth.rate_limit_message(exc))
            raise typer.Exit(code=1)
        except github.InvalidTokenError:
            typer.echo("GitHub rejected the new token as well. Please check your token and try again.")
            raise typer.Exit(code=1)
    except github.RateLimitExceeded as exc:
        typer.echo(auth.rate_limit_message(exc))
        raise typer.Exit(code=1)

    cache.write_cache(keyword, result.total_count, result.repos)
    _emit_results(keyword, result.total_count, result.repos)


def _emit_results(keyword: str, total_count: int, repos: list[github.RepoData]) -> None:
    ranked = bucketing.rank_by_stars(repos)
    bucketed = bucketing.bucket_repos(ranked)

    if bucketed:
        typer.echo(output.render_table(bucketed))
    typer.echo(output.format_verdict(total_count, bucketed))

    csv_path = Path.cwd() / output.csv_filename(keyword)
    output.write_csv(csv_path, bucketed)


if __name__ == "__main__":
    app()
