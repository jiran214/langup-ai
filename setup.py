import setuptools  # 导入setuptools打包工具

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# python setup.py sdist & python setup.py bdist_wheel
# twine upload dist/langup-0.0.5* -u__token__

setuptools.setup(
    name="langup",
    version="0.0.6",
    author="ran",
    author_email="jiran214@qq.com",
    description="社交网络机器人",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jiran214/langup-ai/tree/master",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        'edge_tts==6.1.8',
        'bilibili-api-python==16.1.0',
        'openai==0.28.0',
        'langchain~=0.0.286',
        'ratelimit==2.2.1',
        'pygame~=2.5.1',
        'scipy==1.7.3',
        'httpx~=0.24.1',
        'requests~=2.31.0',
        'pydantic~=2.3.0',
        'urllib3==1.26.17',
        'aiofiles~=23.2.1',
        'setuptools~=65.5.1'
    ]
)
