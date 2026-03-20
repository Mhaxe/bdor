import * as React from "react"
import {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuTrigger,
  NavigationMenuContent,
  NavigationMenuLink,
} from "@/components/ui/navigation-menu"
// Use plain anchors here to avoid requiring a Router context when the
// component is rendered outside of the SPA root (server-side pages, previews, etc.).

type Props = {
  children: React.ReactNode
}

export default function MainLayout({ children }: Props) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="w-full border-b bg-background/50">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <a href="#" onClick={(e) => e.preventDefault()} className="flex items-center gap-3" aria-disabled>
              <img src="/static/balonrank-logo.png" alt="BalonRank logo" className="h-12 w-auto object-contain" />
              <span className="font-semibold text-sm">BalonRank</span>
            </a>
            <NavigationMenu className="flex-none">
              <NavigationMenuList className="flex-none justify-start">
              <NavigationMenuItem>
                <NavigationMenuTrigger>Supported Competitions</NavigationMenuTrigger>
                <NavigationMenuContent>
                  <ul className="grid w-[400px] gap-2 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
                    <li>
                      <NavigationMenuLink asChild>
                        <a href="#" onClick={(e) => e.preventDefault()}>
                          <div className="flex items-center gap-3">
                            <img src="/static/competitions/premier-league.webp" alt="Premier League" loading="lazy" className="w-10 h-10 rounded-md object-contain" />
                            <div className="flex flex-col gap-1 text-sm">
                              <div className="leading-none font-medium">Premier League</div>
                            </div>
                          </div>
                        </a>
                      </NavigationMenuLink>
                    </li>

                    <li>
                      <NavigationMenuLink asChild>
                        <a href="#" onClick={(e) => e.preventDefault()}>
                          <div className="flex items-center gap-3">
                            <img src="/static/competitions/la-liga.webp" alt="La Liga" loading="lazy" className="w-10 h-10 rounded-md object-contain" />
                            <div className="flex flex-col gap-1 text-sm">
                              <div className="leading-none font-medium">La Liga</div>
                            </div>
                          </div>
                        </a>
                      </NavigationMenuLink>
                    </li>

                    <li>
                      <NavigationMenuLink asChild>
                        <a href="#" onClick={(e) => e.preventDefault()}>
                          <div className="flex items-center gap-3">
                            <img src="/static/competitions/bundesliga.webp" alt="Bundesliga" loading="lazy" className="w-10 h-10 rounded-md object-contain" />
                            <div className="flex flex-col gap-1 text-sm">
                              <div className="leading-none font-medium">Bundesliga</div>
                            </div>
                          </div>
                        </a>
                      </NavigationMenuLink>
                    </li>

                    <li>
                      <NavigationMenuLink asChild>
                        <a href="#" onClick={(e) => e.preventDefault()}>
                          <div className="flex items-center gap-3">
                            <img src="/static/competitions/serie-a.webp" alt="Serie A" loading="lazy" className="w-10 h-10 rounded-md object-contain" />
                            <div className="flex flex-col gap-1 text-sm">
                              <div className="leading-none font-medium">Serie A</div>
                            </div>
                          </div>
                        </a>
                      </NavigationMenuLink>
                    </li>

                    <li>
                      <NavigationMenuLink asChild>
                        <a href="#" onClick={(e) => e.preventDefault()}>
                          <div className="flex items-center gap-3">
                            <img src="/static/competitions/ligue-1.webp" alt="Ligue 1" loading="lazy" className="w-10 h-10 rounded-md object-contain" />
                            <div className="flex flex-col gap-1 text-sm">
                              <div className="leading-none font-medium">Ligue 1</div>
                            </div>
                          </div>
                        </a>
                      </NavigationMenuLink>
                    </li>

                    <li>
                      <NavigationMenuLink asChild>
                        <a href="#" onClick={(e) => e.preventDefault()}>
                          <div className="flex items-center gap-3">
                            <img src="/static/competitions/champions-league.webp" alt="Champions League" loading="lazy" className="w-10 h-10 rounded-md object-contain" />
                            <div className="flex flex-col gap-1 text-sm">
                              <div className="leading-none font-medium">Champions League</div>
                            </div>
                          </div>
                        </a>
                      </NavigationMenuLink>
                    </li>

                    <li>
                      <NavigationMenuLink asChild>
                        <a href="#" onClick={(e) => e.preventDefault()}>
                          <div className="flex items-center gap-3">
                            <img src="/static/competitions/europa-league.webp" alt="Europa League" loading="lazy" className="w-10 h-10 rounded-md object-contain" />
                            <div className="flex flex-col gap-1 text-sm">
                              <div className="leading-none font-medium">Europa League</div>
                            </div>
                          </div>
                        </a>
                      </NavigationMenuLink>
                    </li>
                  </ul>
                </NavigationMenuContent>
              </NavigationMenuItem>

              <NavigationMenuItem>
                <NavigationMenuTrigger>FAQs</NavigationMenuTrigger>
                <NavigationMenuContent>
                  <ul className="w-72">
                    <li>
                      <NavigationMenuLink asChild>
                        <a href="#" onClick={(e) => e.preventDefault()}>How are the points calculated?</a>
                      </NavigationMenuLink>
                    </li>
                  </ul>
                </NavigationMenuContent>
              </NavigationMenuItem>
              </NavigationMenuList>
            </NavigationMenu>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        {children}
      </main>
    </div>
  )
}
