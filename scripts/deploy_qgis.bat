:: Configurar nome e caminho de destino do plugin
set PluginName=ibgedatadownloader
set PluginPath=%AppData%\QGIS\QGIS3\profiles\default\python\plugins\%PluginName%

:: Mudar o diretório de trabalho para o diretório deste script e salvar o diretório anterior numa pilha
pushd %~dp0

:: Espelhar o conteúdo atual da pasta de origem na pasta de destino
robocopy "..\%PluginName%" "%PluginPath%" /MIR

:: Retornar ao diretório de trabalho inicial
popd
