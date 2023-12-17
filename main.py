import module_importer


def test_import():
	module_importer.add_import_github_repo(
		'kenny-kvibe', 'flask-pandas-app', 'main')
	import data_app  #type:ignore
	print(data_app.main(5, 5, 0, 9))


def main():
	module_importer.init_logger(module_importer.Logger.ERROR)
	test_import()

	print(module_importer.imported_modules())
	print(module_importer.importer_meta_classes())



if __name__ == '__main__':
	main()
