from setuptools import setup, find_packages

desc = '''
tmux2html captures full tmux windows or individual panes
then parses their contents into HTML.
'''.strip()

setup(
    name='tmux2html',
    version='0.1.11',
    author='Tommy Allen',
    author_email='tommy@esdf.io',
    description=desc,
    packages=find_packages(),
    url='https://github.com/tweekmonster/tmux2html',
    install_requires=[],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'tmux2html=tmux2html.main:main',
        ]
    },
    keywords='tmux html cool hip neat rad',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Topic :: Terminals :: Terminal Emulators/X Terminals',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ]
)
