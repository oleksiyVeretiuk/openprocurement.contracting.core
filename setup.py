from setuptools import setup, find_packages

version = '2.0.1+eacore'

requires = [
    'setuptools',
]

test_requires = requires + [
    'webtest',
    'munch',
    'python-coveralls',
    'openprocurement.tender.belowthreshold',
]

docs_requires = requires + [
    'sphinxcontrib-httpdomain',
]

api_requires = requires + [
    'openprocurement.api>=2.4',
    'openprocurement.tender.core',
]

entry_points = {
    'openprocurement.api.plugins': [
        'contracting.core = openprocurement.contracting.core.includeme:includeme'
    ],
    'openprocurement.api.migrations': [
        'contracting = openprocurement.contracting.core.migration:migrate_data'
    ],
    'transferring': [
        'contracting.transferring = openprocurement.contracting.core.plugins.transferring.includeme:includeme'
    ]
}

setup(name='openprocurement.contracting.core',
      version=version,
      description="",
      long_description=open("README.rst").read(),
      classifiers=[
          "Framework :: Pylons",
          "License :: OSI Approved :: Apache Software License",
          "Programming Language :: Python",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
      ],
      keywords="web services",
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      license='Apache License 2.0',
      url='https://github.com/openprocurement/openprocurement.contracting.core',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['openprocurement', 'openprocurement.contracting'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      extras_require={
          'api': api_requires,
          'test': test_requires,
          'docs': docs_requires
      },
      entry_points=entry_points,
      )
