const { app, BrowserWindow } = require('electron')
const { exec } = require('child_process')
const path = require('path')
const http = require('http')

let mainWindow

function waitForBackend(retries = 20, delay = 1000) {
    return new Promise((resolve, reject) => {
        const attempt = () => {
            http.get('http://localhost:8003', (res) => {
                resolve()
            }).on('error', () => {
                if (retries-- > 0) {
                    console.log(`[BACKEND] Esperando... (intentos restantes: ${retries})`)
                    setTimeout(attempt, delay)
                } else {
                    reject(new Error('Backend no respondió después de varios intentos'))
                }
            })
        }
        attempt()
    })
}

app.whenReady().then(async () => {
    const isDev = !app.isPackaged

    const rootPath = isDev
        ? path.join(__dirname, '..')
        : process.resourcesPath

    const pythonPath = isDev
        ? 'python'
        : path.join(process.resourcesPath, 'python-embed', 'python.exe')

    console.log("🚀 Iniciando backend...")
    console.log("📂 Root path:", rootPath)
    console.log("🐍 Python path:", pythonPath)

    const backend = exec(
        `"${pythonPath}" -m uvicorn backend.main:app --port 8003`,
        {
            cwd: rootPath,
            env: { ...process.env, FOOTBALL_DATA_KEY: 'b17b0d2033f04fd498bf07facc655eb6' }
        }
    )

    backend.stdout.on('data', (data) => console.log(`[BACKEND]: ${data}`))
    backend.stderr.on('data', (data) => console.error(`[BACKEND ERROR]: ${data}`))
    backend.on('close', (code) => console.log(`[BACKEND CLOSED]: ${code}`))

    try {
        await waitForBackend()
        console.log("✅ Backend listo!")
    } catch (e) {
        console.error("❌ Backend no inició:", e.message)
    }

    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
    })

    mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'))
    mainWindow.webContents.openDevTools()
})