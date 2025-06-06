from setuptools import setup, find_packages

setup(
    name='LLMTenderBot',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        # List your project dependencies here, e.g.,
        # 'requests==2.28.1',
        'python-telegram-bot==22.1',
        'python-dotenv==1.1.0',
        'pydantic==2.10.3',
        'pydantic-settings==2.3.0'
    ],
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