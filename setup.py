from setuptools import setup, find_packages
setup(
    name = 'mongoqt',
    version = '0.1.0',
    description = 'framework to create mongodb app based on pyqt5',
    author = 'Jackey Qiu',
    author_email = 'canrong.qiu@desy.de',
    url = 'https://github.com/jackey-qiu/mongoqt',
    classifiers = ['Topic::pyqt5 application', 'Programming Language::Python'],
    license = 'MIT',
    install_requires = ['PyQt5', 'pyqtgraph', 'qdarkstyle', 'numpy', 'pymongo', 'bcrypt', 'pandas', 'dnspython', 'pyyaml'],
    packages = find_packages(),
    package_data = {'mongoqt.gui.resource': ['config/*', 'ui/dialogue_ui/*','ui/icons/*']},
    scripts = [],
     entry_points = {
         'console_scripts' : [
             'mongoqt = mongoqt.bin.app_launcher:start_app',
         ],
     }
)