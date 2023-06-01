# Releasing to PyPI

ref:<https://zenn.dev/sikkim/articles/490f4043230b5a>

## Creating Packages

```shell
python setup.py sdist
python setup.py bdist_wheel
```

## Upload to TEST environment of PyPI

```shell
twine upload --repository testpypi dist/*
```

## Upload to MAIN environment of PyPI

```shell
twine upload --repository pypi dist/*
```
