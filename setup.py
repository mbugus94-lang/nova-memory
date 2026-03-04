from setuptools import setup, find_packages

setup(
    name="nova-memory",
    version="2.0.0",
    description="Real-Time AI Agent Memory Management System",
    author="David Gakere",
    author_email="mbugus94@gmail.com",
    url="https://github.com/mbugus94-lang/nova-memory",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.0.0",
        "numpy>=1.24.0",
        "torch>=2.0.0",
        "sentence-transformers>=2.2.0",
        "plyvel>=1.5.0",
        "solana>=0.30.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
