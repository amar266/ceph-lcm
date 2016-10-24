# -*- coding: utf-8 -*-
"""CLI methods for password reset."""


from __future__ import absolute_import
from __future__ import unicode_literals

import click

from cephlcm_cli import decorators
from cephlcm_cli import main


@main.cli_group
def password_reset():
    """Password reset subcommands"""


@click.argument("user-id", type=click.UUID)
@decorators.command(password_reset)
def reset(client, user_id):
    """Request password reset for user with given ID."""

    return client.request_password_reset(str(user_id))


@click.argument("password-reset-token")
@decorators.command(password_reset)
def peek(client, password_reset_token):
    """Checks if password reset token still valid."""

    return client.peek_password_reset(password_reset_token)


@click.argument("password-reset-token")
@click.password_option(help="New password")
@decorators.command(password_reset)
def new(client, password, password_reset_token):
    """Update password for the given password reset token.

    If no password is set in CLI, interactive prompt will request to
    enter it.
    """

    return client.reset_password(password_reset_token, password)
