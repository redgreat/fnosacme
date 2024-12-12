# fnacme
飞牛Nas，通过acme自动申请，自动部署、刷新https证书。

运行步骤：

1.需安装OpenSSL包
```shell
sudo apt install python3-openssl
```

2.下载安装包
```shell
mkdir -p /vol1/tools
cd tools
git clone https://github.com/redgreat/fnosacme.git
```

3.添加执行权限
```shell
cd fnosacme
chmod +x cert-up.sh
```

4.修改配置文件
```shell
vim config

# 你主域名，如 baidu.com sina.com.cn 等
export DOMAIN=
### 只测试了 全局域名baidu.com样式

# DNS类型，根据域名服务商而定
export DNS=dns_dp

# DNS API 生效等待时间 值(单位：秒)
# 某些域名服务商的API生效时间较大，需要将这个值加大(比如900)
export DNS_SLEEP=120

# 阿里云 DNS=dns_ali
#export Ali_Key="LTqIA87hOKdjevsf5"
#export Ali_Secret="0p5EYueFNq501xnCPzKNbx6K51qPH2"

# Dnspod DNS=dns_dp
export DP_Id="123456"
export DP_Key="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Godaddy DNS=dns_gd
#export GD_Key="sdfsdfsdfljlbjkljlkjsdfoiwje"
#export GD_Secret="asdfsdfsfsdfsdfdfsdf"

# AWS DNS=dns_aws
#export AWS_ACCESS_KEY_ID="sdfsdfsdfljlbjkljlkjsdfoiwje"
#export AWS_SECRET_ACCESS_KEY="xxxxxxx"

# Linode DNS=dns_linode
#export LINODE_API_KEY="xxxxxxxx"

```

5.手动执行
```shell
sh cert-up.sh
```

6.添加定时任务，每月15日0点05执行
```shell
crontab -e
5 0 15 * * /vol1/tools/fnosacme/cert-up.sh update >> /vol1/tools/fnosacme/run.log 2>&1
```

