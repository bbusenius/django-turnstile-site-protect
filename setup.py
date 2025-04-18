from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='django-turnstile-site-protect',
    version='0.1.0',
    author='Brad Busenius',
    author_email='YOUR_EMAIL@example.com',  # Update with your actual email
    description='A Django package for site-wide protection using Cloudflare Turnstile',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/USERNAME/django-turnstile-site-protect',  # Update with your GitHub username
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=3.2',
        'requests>=2.25.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security',
    ],
    python_requires='>=3.7',
)