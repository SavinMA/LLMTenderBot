from setuptools import setup, find_packages

setup(
    name='LLMTenderBot',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        # Core dependencies
        'python-telegram-bot==22.1',
        'python-dotenv==1.1.0',
        'pydantic==2.10.3',
        'pydantic-settings==2.3.0',
        
        # LLM and AI dependencies
        'ollama>=0.4.1',
        'mistralai>=1.2.0',
        'httpx>=0.28.1',
        
        # Document processing
        'docling>=2.8.1',
        
        # Text processing and splitting
        'semantic-text-splitter>=0.15.0',
        'tokenizers>=0.21.0',
        
        # Logging and utilities
        'loguru>=0.7.2',
        'telegramify-markdown>=0.1.2',
    ],
    extras_require={
        'dev': [
            'pytest>=8.0.0',
            'black>=24.0.0',
            'flake8>=7.0.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'llmtenderbot=telegram_bot:main',
        ],
    },
    author='SavinMA',
    author_email='ctok81@gmail.com',
    description='LLM Tender Bot',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/SavinMA/LLMTenderBot',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
) 