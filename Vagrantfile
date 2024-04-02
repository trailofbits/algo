Vagrant.configure("2") do |config| 
  config.vm.box = "bento/ubuntu-20.04" 
  
  config.vm.provider "virtualbox" do |v| 
    v.name = "algo-20.04"
    v.memory = "512" 
    v.cpus = "1" 
  end

  config.vm.synced_folder "./", "/opt/algo", create: true

  config.vm.provision "ansible_local" do |ansible|
    ansible.playbook = "/opt/algo/main.yml"

    # https://github.com/hashicorp/vagrant/issues/12204
    ansible.pip_install_cmd = "sudo apt-get install -y python3-pip python-is-python3 && sudo ln -s -f /usr/bin/pip3 /usr/bin/pip"
    ansible.install_mode = "pip_args_only"
    ansible.pip_args = "-r /opt/algo/requirements.txt"
    ansible.inventory_path = "/opt/algo/inventory"
    ansible.limit = "local"
    ansible.verbose = "-vvvv"
    ansible.extra_vars = {
      provider: "local",
      server: "localhost",
      ssh_user: "",
      endpoint: "127.0.0.1",
      ondemand_cellular: true,
      ondemand_wifi: false,
      dns_adblocking: true,
      ssh_tunneling: true,
      store_pki: true,
      tests: true,
      no_log: false
    }
  end
end
