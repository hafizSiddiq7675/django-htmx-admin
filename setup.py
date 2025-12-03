"""
Setup script for django-htmx-admin.

HTMX-Powered Django Admin Enhancement
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8") if (this_directory / "README.md").exists() else ""

setup(
    name="django-htmx-admin",
    version="1.0.3",
    author="django-htmx-admin",
    author_email="",
    description="HTMX-Powered Django Admin Enhancement",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/django-htmx-admin",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    package_data={
        "htmx_admin": [
            "templates/htmx_admin/*.html",
            "templates/htmx_admin/partials/*.html",
            "templates/htmx_admin/grappelli/*.html",
            "static/htmx_admin/*.js",
            "static/htmx_admin/*.css",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Django>=4.0",
        "django-htmx>=1.14.0",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-django",
            "coverage",
            "flake8",
            "black",
            "isort",
        ],
    },
    keywords=[
        "django",
        "admin",
        "htmx",
        "ajax",
        "inline-editing",
        "modal",
        "toast",
    ],
    project_urls={
        "Documentation": "https://github.com/yourusername/django-htmx-admin#readme",
        "Source": "https://github.com/yourusername/django-htmx-admin",
        "Bug Tracker": "https://github.com/yourusername/django-htmx-admin/issues",
    },
)
