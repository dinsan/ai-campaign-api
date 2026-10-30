"""Shared test configuration.

Tests that import the FastAPI application need application settings to exist.
These defaults only apply when the variables are not already set, so a real
environment (or CI configuration) always takes precedence. No connection is
made to the database during the unit tests.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "unit-test-secret-key-not-used-for-real-tokens")
