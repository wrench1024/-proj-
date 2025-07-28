@echo off
echo ========================================
echo RegDoc Frontend �ۺϲ���
echo ========================================
echo.

echo [1] �������...
echo.
node --version
echo.
if exist "node_modules" (
    echo ? node_modules ����
) else (
    echo ? node_modules ������
    echo ������: npm install
    goto :end
)

echo.
echo [2] ��Ŀ�ļ����...
if exist "src\App.vue" (
    echo ? ���������
) else (
    echo ? �����ȱʧ
)

if exist "src\main.ts" (
    echo ? ����ļ�����
) else (
    echo ? ����ļ�ȱʧ
)

if exist "package.json" (
    echo ? �����ļ�����
) else (
    echo ? �����ļ�ȱʧ
)

echo.
echo [3] �������...
if exist "node_modules\vue" (
    echo ? Vue 3 �Ѱ�װ
) else (
    echo ? Vue 3 δ��װ
)

if exist "node_modules\element-plus" (
    echo ? Element Plus �Ѱ�װ
) else (
    echo ? Element Plus δ��װ
)

if exist "node_modules\vite" (
    echo ? Vite �Ѱ�װ
) else (
    echo ? Vite δ��װ
)

echo.
echo [4] ��������...
echo ���ڹ�����Ŀ...
node node_modules\vite\bin\vite.js build > build_output.log 2>&1

if %errorlevel% equ 0 (
    echo ? �����ɹ�
    if exist "dist\index.html" (
        echo ? ����ļ����ɳɹ�
    ) else (
        echo ? ����ļ�����ʧ��
    )
) else (
    echo ? ����ʧ��
    echo �鿴 build_output.log �˽�����
)

echo.
echo [5] �ļ���Сͳ��...
if exist "dist" (
    for %%f in (dist\*.*) do echo   %%~nxf: %%~zf bytes
    for %%f in (dist\assets\*.*) do echo   assets\%%~nxf: %%~zf bytes
)

echo.
echo [6] �����Ԥ��...
echo ����ͨ�����·�ʽԤ��Ӧ��:
echo 1. ֱ�Ӵ�: file:///%CD%\dist\index.html
echo 2. ʹ���κ�HTTP�������ṩ dist/ Ŀ¼
echo.

echo ========================================
echo �������!
echo ========================================
echo.
echo �������һ��:
echo 1. ��������ɹ���Ӧ����׼���ò���
echo 2. ʹ��HTTP������Ԥ����������
echo 3. ��������������Web������
echo.

:end
pause
