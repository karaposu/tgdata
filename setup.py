import re
from pathlib import Path

from setuptools import setup, find_packages


def read_version():
    """Single source of truth: parse __version__ from tgdata/__init__.py.

    Parsed (not imported) so it works before dependencies are installed.
    """
    init_py = Path(__file__).parent / 'tgdata' / '__init__.py'
    match = re.search(
        r'^__version__\s*=\s*["\']([^"\']+)["\']',
        init_py.read_text(encoding='utf-8'),
        re.MULTILINE,
    )
    if not match:
        raise RuntimeError('Unable to find __version__ in tgdata/__init__.py')
    return match.group(1)


setup(
    name='tgdata',  # Package name
    version=read_version(),  # Single source of truth: tgdata/__init__.py
    author='enes kuzucu',  # Your name
    
    description='A production-grade Python library for extracting and processing Telegram group and channel messages', 
    long_description=open('README.md').read(),  # Long description from a README file
    long_description_content_type='text/markdown',  # Type of the long description
    
    packages=find_packages(),  # Automatically find packages in the directory
    install_requires=[
        # Group operations use 1.45's wrapped join results and tested send seam.
        # 2.0 is a breaking API rewrite; re-run offline suites on SDK upgrades.
        'Telethon>=1.45.0,<2.0',
        # Required by the existing message/discovery DataFrame APIs. Nullable Int64
        # (used for GroupedId album ids > 2^53) needs pandas >= 1.0.
        'pandas>=1.0',
    ],
    extras_require={
        # Only needed when the config sets `proxy = socks5://…` (or socks4 / http).
        'proxy': ['python-socks[asyncio]>=2.0'],
    },

    classifiers=[
        'Development Status :: 3 - Alpha',  # Development status
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # License as you choose
        'Programming Language :: Python :: 3',  # Supported Python versions
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',  # Minimum version requirement of Python
)
