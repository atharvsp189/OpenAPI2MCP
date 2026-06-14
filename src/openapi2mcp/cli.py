from __future__ import annotations

import click

from openapi2mcp.generator import generate


@click.group()
def cli():
    """Generate an MCP server from a Swagger/OpenAPI spec."""


@cli.command(name="generate")
@click.option("--spec", required=True, help="OpenAPI/Swagger spec URL or file path")
@click.option("--out", "out_dir", required=True, help="Output directory for the generated server")
@click.option(
    "--name",
    "server_name",
    default="generated-mcp",
    show_default=True,
    help="Name for the generated MCP server",
)
def generate_command(spec, out_dir, server_name):
    tools, skipped = generate(spec, out_dir, server_name)
    click.echo(f"Registered {len(tools)} tools:")
    for tool in tools:
        click.echo(f"  - {tool.name}  [{tool.method.upper()} {tool.path}]")
    for name, reason in skipped:
        click.echo(f"  SKIPPED {name}: {reason}")


def main():
    cli()
