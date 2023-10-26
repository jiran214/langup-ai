import setuptools  # 导入setuptools打包工具
from langup import __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# python setup.py sdist & python setup.py bdist_wheel
# twine upload dist/langup-0.0.10* -u__token__


setuptools.setup(
    name="langup",
    version=__version__,
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
    install_requires=[line.strip() for line in open(file='./requirements.txt').readlines() if line]
)
