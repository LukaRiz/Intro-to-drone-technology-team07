from setuptools import setup

package_name = 'idt'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Kjeld Jensen, SDU Drone Center',
    maintainer_email='kjen@sdu.dk',
    description='IDT - Introduction to Drone Technology',
    license='BSD 3-Clause',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
                 'hello_drone = idt.hello_drone:main',
                 'get_global_pos = idt.get_global_pos:main',
                 'upload_waypoints = idt.upload_waypoints:main',
                'get_radio_rssi = idt.get_radio_rssi:main',
        ],
    },
)
