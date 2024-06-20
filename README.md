# AltaDB SDK

## Example Usage

### Set up configuration

```sh
altadb config add
```
- Above command will prompt you to enter the following details:
    - Org ID
    - API Key
    - API Secret
    - API URL


### Upload a file

- `path` can be a file or a directory. In case of a directory, all files in the directory will be uploaded recursively.
```sh
altadb upload <dataset> <path>
```