# automation

## installation
	git clone https://github.com/dstoffel/automation.git
	cd automation
	cp config.py.sampe config.py
	sudo cp initscript /etc/init.d/automation
	sudo sed -i "s/_RUNAS_/$(whoami)/" /etc/init.d/automation
	sudo sed -i "s/_FOLDER_/$(pwd | sed 's/\//\\\//g')/" /etc/init.d/automation
	sudo chmod +x /etc/init.d/automation
	sudo update-rc.d automation defaults
## start
sudo /etc/init.d/automation start

## Log
tail -f /var/log/automation.log
