import setuptools  # 导入setuptools打包工具

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# python setup.py sdist
# python setup.py bdist_wheel
# twine upload dist/langup-0.0.x*

setuptools.setup(
    name="langup",
    version="0.0.1",
    author="ran",
    author_email="jiran214@qq.com",
    description="社交网络机器人",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jiran214/langup/tree/master/src",
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
