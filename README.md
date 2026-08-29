# Windows 10 Docker
Docker vps:

docker run -p 6688:80 dorowu/ubuntu-desktop-lxde-vnc

Chạy Windows 10 trên VPS bằng Docker và KVM.

## 1. Cài đặt thư viện

```bash
sudo apt update
sudo apt install docker.io docker-compose -y
```

## 2. Kiểm tra Docker & Docker Compose

```bash
docker -v
docker compose version
```

## 3. Tạo file Docker Compose

Tạo file:

```bash
nano windows10.yml
```

Sau đó thêm nội dung sau:

```yaml
version: "3.8"

services:
  windows:
    image: dockurr/windows
    container_name: windows

    environment:
      VERSION: "10"
      USERNAME: "MASTER"
      PASSWORD: "admin@123"
      RAM_SIZE: "8G"
      CPU_CORES: "4"
      DISK_SIZE: "600G"
      DISK2_SIZE: "200G"

    devices:
      - /dev/kvm
      - /dev/net/tun

    cap_add:
      - NET_ADMIN

    ports:
      - "8006:8006"
      - "3389:3389/tcp"
      - "3389:3389/udp"

    stop_grace_period: 2m
```

Lưu file:

```text
CTRL + O
ENTER
CTRL + X
```

## 4. Kiểm tra KVM

Kiểm tra xem `/dev/kvm` có tồn tại không:

```bash
ls -la /dev/kvm
```

Nếu có kết quả tương tự:

```text
crw-rw---- 1 root kvm ... /dev/kvm
```

thì KVM đã được bật.

Nếu bị lỗi quyền:

```bash
sudo usermod -aG kvm $USER
newgrp kvm
```

Sau đó kiểm tra lại:

```bash
ls -la /dev/kvm
```

## 5. Chạy Windows 10

Chạy container bằng Docker Compose:

```bash
sudo docker-compose -f windows10.yml up -d
```

Kiểm tra container:

```bash
sudo docker ps
```

Nếu container đang chạy, bạn sẽ thấy:

```text
windows
```

## 6. Truy cập Windows

Sau khi container khởi động, có thể truy cập giao diện Web UI bằng:

```text
http://IP-VPS:8006
```

Hoặc kết nối bằng Remote Desktop:

```text
IP-VPS:3389
```

Thông tin đăng nhập:

```text
Username: MASTER
Password: admin@123
```

## 7. Các lỗi thường gặp

### `no configuration file provided`

Nếu gặp lỗi:

```text
no configuration file provided
```

Hãy chỉ rõ file Compose:

```bash
sudo docker-compose -f windows10.yml up -d
```

### `Cannot access /dev/kvm`

Kiểm tra KVM:

```bash
ls -la /dev/kvm
```

Nếu `/dev/kvm` không tồn tại, VPS có thể chưa hỗ trợ hoặc chưa bật KVM.

### `permission denied on /dev/kvm`

Thêm user vào nhóm `kvm`:

```bash
sudo usermod -aG kvm $USER
newgrp kvm
```

Sau đó kiểm tra:

```bash
ls -la /dev/kvm
```

### `image not found`

Thử tải image:

```bash
sudo docker pull dockurr/windows
```

Sau đó chạy lại:

```bash
sudo docker-compose -f windows10.yml up -d
```

### Container tự thoát

Kiểm tra log:

```bash
sudo docker logs windows
```

Xem trạng thái container:

```bash
sudo docker ps -a
```

Nếu container có trạng thái `Exited`, hãy xem log để xác định nguyên nhân:

```bash
sudo docker logs --tail 100 windows
```

## 8. Kiểm tra tốc độ mạng VPS

Bạn có thể kiểm tra tốc độ mạng tại:

https://fast.com

## 9. Tham khảo

- https://github.com/dockur/windows
- https://docs.docker.com/engine/install/
- https://docs.docker.com/compose/

## 10. Gỡ cài đặt

Dừng và xóa container:

```bash
sudo docker-compose -f windows10.yml down
```

Xóa Docker và Docker Compose:

```bash
sudo apt remove docker.io docker-compose -y
```

Nếu muốn xóa image Windows:

```bash
sudo docker rmi dockurr/windows
```

## 11. Kiểm tra toàn bộ hệ thống

Kiểm tra Docker:

```bash
docker -v
```

Kiểm tra Docker Compose:

```bash
docker compose version
```

Kiểm tra KVM:

```bash
ls -la /dev/kvm
```

Kiểm tra container:

```bash
sudo docker ps -a
```

Xem log:

```bash
sudo docker logs windows
```
