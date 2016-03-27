from setuptools import setup


setup(
    name='tmux2html',
    author='Tommy Allen',
    author_email='tommy@esdf.io',
    entry_points={
        'console_scripts': [
            'tmux2html=tmux2html.main:main',
        ]
    }
)
