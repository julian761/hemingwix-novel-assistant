#!/usr/bin/env python3
"""
Setup script for Hemingwix Notion MCP Server
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="hemingwix-notion-mcp",
    version="1.0.0",
    author="Hemingwix Project",
    author_email="contact@hemingwix.com",
    description="Model Context Protocol server for Notion database integration in novel writing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/hemingwix-novel-assistant",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Text Processing :: General",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0", 
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "hemingwix-notion-mcp=server:main",
        ],
    },
    keywords="mcp, notion, novel, writing, ai, assistant, database",
    project_urls={
        "Bug Reports": "https://github.com/your-username/hemingwix-novel-assistant/issues",
        "Source": "https://github.com/your-username/hemingwix-novel-assistant",
        "Documentation": "https://github.com/your-username/hemingwix-novel-assistant/blob/main/mcp_server/README.md",
    },
)