:content_order: 30
:content_title: Configuration Parameters

Settings Reference
==================

The component relies on a single configuration file, `config.ini`.

### Required Parameters

+-----------+------+---------+-----------------------------+
| Parameter | Type | Default | Description                 |
+===========+======+=========+=============================+
| HOST\_IP  | str  | 127.0.0.1 | The service host address. |
+-----------+------+---------+-----------------------------+
| PORT      | int  | 8080    | The listening port.         |
+-----------+------+---------+-----------------------------+

All changes require a restart of the component service.