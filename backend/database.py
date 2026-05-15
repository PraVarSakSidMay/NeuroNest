"""
Supabase client initialisation for the NeuroNest Journal API.

The service-role key is used so that the backend can bypass RLS when
performing server-side operations.  Row-level security is still enforced
at the query level by always filtering on ``user_id``.
"""

import os

from supabase import Client, create_client


def get_supabase() -> Client:
    """Return an initialised Supabase client.

    Reads ``SUPABASE_URL`` and ``SUPABASE_SERVICE_ROLE_KEY`` from the
    environment.  Both variables must be set before the application starts.

    Returns:
        A configured :class:`supabase.Client` instance.

    Raises:
        RuntimeError: If either environment variable is absent or empty.
    """
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

    if not url:
        raise RuntimeError(
            "SUPABASE_URL environment variable is not set. "
            "The application cannot connect to the database."
        )
    if not key:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY environment variable is not set. "
            "The application cannot connect to the database."
        )

    return create_client(url, key)


# Module-level singleton — created once on import so that all request
# handlers share the same connection pool.
supabase: Client = get_supabase()
