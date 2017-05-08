Vagrant.configure(2) do |config|

  config.vm.box_url = 'https://atlas.hashicorp.com/ARTACK/boxes/debian-jessie'
  config.vm.box = "ARTACK/debian-jessie"

  # uncomment below if you want to have public network bridge access
  # you might need to adjust the interface name, refer to Vagrant documentation
  # for how to set it properly

  # config.vm.network "public_network", bridge: "en0: Wi-Fi (AirPort)"

  config.vm.network "forwarded_port", guest: 8000, host: 8000

  $script = <<SCRIPT
rm -rf /vagrant/venv
rm -rf /vagrant/node_modules
apt-get update
apt-get install -y curl python-dev python-pip python-virtualenv libxml2-dev \
libxslt1-dev libpq-dev libffi-dev libjpeg-dev libturbojpeg1-dev libjpeg62-turbo-dev \
git build-essential libtiff5-dev libopenjp2-7-dev libfreetype6-dev libwebp-dev nodejs npm
cd /vagrant
virtualenv venv
ln -s /usr/bin/nodejs /usr/bin/node
source venv/bin/activate
pip install --upgrade -r requirements.txt
npm config set color false
npm install
npm install core-js
./node_modules/.bin/grunt --no-color
python manage.py migrate
python manage.py populatedb --createsuperuser
python manage.py runserver 0:8000
SCRIPT

  config.vm.provision "shell", inline: $script

end
