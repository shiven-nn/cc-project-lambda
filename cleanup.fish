# Stop services
sudo systemctl stop docker.service docker.socket
sudo systemctl stop containerd

# Remove specific runsc file
sudo rm -f /var/lib/docker/runtimes/runsc.K2HJQ2P694WSC115W2D199-45F6ZL8LM-XSX8YGMW6R2S8KMTQ10====

# Clean all runsc runtime files
if test -d /var/lib/docker/runtimes
    sudo rm -rf /var/lib/docker/runtimes/runsc* 2>/dev/null
end

# Clean containerd tasks
if test -d /run/containerd/io.containerd.runtime.v2.task
    sudo rm -rf /run/containerd/io.containerd.runtime.v2.task/* 2>/dev/null
end
if test -d /run/containerd/runc
    sudo rm -rf /run/containerd/runc/* 2>/dev/null
end

# Verify cleanup
sudo ls -la /var/lib/docker/runtimes/
sudo ls -la /run/containerd/io.containerd.runtime.v2.task/
