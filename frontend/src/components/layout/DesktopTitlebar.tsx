import React, { useEffect, useState } from "react";
import { Minus, Square, X } from "lucide-react";

const isDesktop =
  typeof window !== "undefined" &&
  ((window as any).__TAURI_INTERNALS__ !== undefined || navigator.userAgent.includes("Tauri"));

export const DesktopTitlebar: React.FC = () => {
  const [appWindow, setAppWindow] = useState<any>(null);
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    let mounted = true;

    const init = async () => {
      if (!isDesktop) return;
      const windowApi = await import("@tauri-apps/api/window");
      const current = windowApi.getCurrentWindow();
      if (!mounted) return;

      setAppWindow(current);
      setIsMaximized(await current.isMaximized());
    };

    init();

    return () => {
      mounted = false;
    };
  }, []);

  if (!isDesktop) return null;

  const handleWindowAction = async (action: "minimize" | "maximize" | "close") => {
    if (!appWindow) return;

    if (action === "minimize") {
      await appWindow.minimize();
      return;
    }

    if (action === "maximize") {
      const maximized = await appWindow.isMaximized();
      if (maximized) {
        await appWindow.unmaximize();
        setIsMaximized(false);
      } else {
        await appWindow.maximize();
        setIsMaximized(true);
      }
      return;
    }

    await appWindow.close();
  };

  return (
    <div
      className="h-10 w-full bg-linear-to-r from-[#0c1636] via-[#11224a] to-[#0b1737] border-b border-secondary/25 flex items-center justify-between px-3 select-none"
    >
      <div
        data-tauri-drag-region
        className="flex items-center gap-2 min-w-0 flex-1 h-full"
        onDoubleClick={() => handleWindowAction("maximize")}
      >
        <div className="w-2 h-2 rounded-full bg-secondary/80" />
        <span className="text-xs font-semibold tracking-[0.14em] text-secondary truncate">KARCHAIN CASINO DESK</span>
      </div>

      <div className="flex items-center gap-1 ml-3">
        <button
          type="button"
          onClick={() => handleWindowAction("minimize")}
          className="w-7 h-7 rounded-md text-muted hover:text-white hover:bg-white/10 transition-colors flex items-center justify-center"
          aria-label="Minimize"
          title="Minimize"
        >
          <Minus size={14} />
        </button>
        <button
          type="button"
          onClick={() => handleWindowAction("maximize")}
          className="w-7 h-7 rounded-md text-muted hover:text-white hover:bg-white/10 transition-colors flex items-center justify-center"
          aria-label={isMaximized ? "Restore" : "Maximize"}
          title={isMaximized ? "Restore" : "Maximize"}
        >
          <Square size={11} />
        </button>
        <button
          type="button"
          onClick={() => handleWindowAction("close")}
          className="w-7 h-7 rounded-md text-muted hover:text-white hover:bg-red-500/80 transition-colors flex items-center justify-center"
          aria-label="Close"
          title="Close"
        >
          <X size={14} />
        </button>
      </div>
    </div>
  );
};
