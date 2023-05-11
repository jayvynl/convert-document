# convert-document

A docker container environment to bundle the execution of `LibreOffice` to convert documents of various types (such as Word, OpenDocument, etc.) to PDF. An instance of `LibreOffice` will be run in the background, and controlled via a local socket (i.e. the UNO protocol).

## Usage

This service is intended for use exclusively as a docker container. While it may be possible to
run this application stand-alone, this is not recommended. For normal usage, you should pull the
latest stable image off DockerHub and run it like this:

```shell
make build
docker run -p 3000:3000 -ti convert-document
```

Once the service has initialised, files can be sent to the root endpoint, and a PDF version
will be returned as a download:

```shell
curl -o out.pdf -F format=pdf -F 'file=@mydoc.doc' http://localhost:3000
```

## Development

To build, run:

```shell
meke build
```

To get a development shell:

```shell
make shell
```

## License

MIT, see `LICENSE`.


## Troubleshooting

* `LibreOffice` keeps crashing on startup with `Fatal exception: Signal 11`

If [AppArmor](https://help.ubuntu.com/community/AppArmor) is running on the host machine, it may be blocking `LibreOffice` from starting up.
Try disabling the `AppArmor` profiles related to `LibreOffice` by following these instructions: [https://askubuntu.com/a/1214363](https://askubuntu.com/a/1214363)
