import module_importer


def test_import():
	module_importer.init_logger(module_importer.Logger.ERROR)

	# import  "data_app.py"
	# from    "https://github.com/kenny-kvibe/flask-pandas-app"

	module_importer.add_import_github_repo(
		'kenny-kvibe', 'flask-pandas-app', 'main')
	import data_app  #type:ignore

	print(data_app.main(5, 5, 0, 9))

	# print(module_importer.imported_modules())
	# print(module_importer.importer_meta_classes())


def main() -> int:
	test_import()
	return 0


if __name__ == '__main__':
	raise SystemExit(main())
