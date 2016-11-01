# Windless

基于 Python3 的个人博客,使用 Redis 作为数据库,并具有完全的异步处理支持.

## Feature
  
  - 实现完全异步处理支持 (aiohttp)
  - 进一步封装 aioredis 以适应所需数据操作
  - 使用 Docker 简化安装
  - ~~使用 GitHook 自动化部署~~

## Getting started

### 安装 Docker

ArchLinux:  
`$ pacman -S docker`

Ubuntu:  
`$ wget -qO- https://get.docker.com/ | sh`

如果您在安装 Docker 时速度较慢，可以使用 [Daocloud](https://www.daocloud.io/) 提供的国内加速服务来安装 Docker  
`$ curl -sSL https://get.daocloud.io/docker | sh`

### 构建

进入 dockerfiles 文件夹  
`$ cd dockerfiles/windless`

构建镜像  
`$ docker build -t="windless/v1" .`

如构建镜像时速度依旧很慢, 依然可以使用上面所提及的 Daocloud 进行镜像加速, 按下不表

### 配置

将 core 目录下的 eternity_default.yaml 文件内的所有内容复制到 eternity.yaml 中, 按自己实际情况修改

| name     | about              |
| :------: | :-----------------:|
|env       | 开发环境信息, 无需修改|
|info      | 版本信息, 无需修改|
|server    | 服务器运行的地址、端口|
|memory    | Redis 服务的地址、端口及数据前缀名|
|admin     | 管理员账号密码|
|blog      | 博客的相关信息|

### 运行

使用 docker-compose 运行  
`$ docker-compose up -d`

然后访问 localhost:port 来访问查看是否正常运行


## License

Windless is licensed under [MIT](http://opensource.org/licenses/MIT)
