# manim-scene360
用 manim 来做全景视频！

## 依赖
[manimgl](https://github.com/3b1b/manim)

## 使用方法
只需要让你编写的场景从 `Scene360` 而非 `Scene` 继承来即可。即代码类似于：

```python
class MyScene(Scene360):
    def contruct(self):
        pass
```

但你必须将结果输出到文件。输出的结果会是立方体投影格式的视频，需要使用 FFmpeg 将其转化为全景视频。

`Scene360` 中 `camera.frame.get_center()` 将代表摄像机的位置。

## 存在的问题
- 暂不支持让物体 `fix_in_frame`（这会使其在画面中出现六次）；
- 创建 `Square3D` 等平面时，需要加上参数 `resolution=(10, 10)`（具体值可以视情况更改）；类似地，创建 `Cube` 时，需要加上参数 `square_resolution=(10,10)`；原因在于 OpenGL 在求一点颜色时会将顶点颜色线性插值，然而其并不一定是该点的实际颜色；
- 离摄像机较近的位置若有物体，可能会出现问题，原因未知。
