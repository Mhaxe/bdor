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
          <a href="#" onClick={(e) => e.preventDefault()} className="flex items-center gap-3" aria-disabled>
            <img src="/static/balonrank-logo.png" alt="BalonRank logo" className="h-12 w-auto object-contain" />
            <span className="font-semibold text-sm">BalonRank</span>
          </a>
          <NavigationMenu>
            <NavigationMenuList>
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
                            <img src="https://imgs.search.brave.com/nUfwOZT1rMiBec-eSRm8GMIRC97LgEy_9FRnu_6D8i4/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9pbWFn/ZXMuc2Vla2xvZ28u/Y29tL2xvZ28tcG5n/LzIwLzEvYnVuZGVz/bGlnYS1sb2dvLXBu/Z19zZWVrbG9nby0y/MDcwMDIucG5n" alt="Bundesliga" loading="lazy" className="w-10 h-10 rounded-md object-contain" />
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
                            <img src="https://imgs.search.brave.com/EDBa02IQxW8gK6rQ3V6tifrpcUAfV9laY_vGG-15x9A/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9ibG9n/Z2VyLmdvb2dsZXVz/ZXJjb250ZW50LmNv/bS9pbWcvYi9SMjl2/WjJ4bC9BVnZYc0Vq/TFo5UVNQRnk4WC0y/dDZ1U19ub3ZabENM/a2NCWDNJUVRxSDE0/UXk3cEJxaDdlZzRH/YkxBdFBtalg5aVBW/R3dCd2czU1dmX1c0/TGNtQ3RITngzNWcy/UHFNdUxfZFhVeGtH/VVVqMGVLMGM0Y1pR/NHQ1bk1mYUVISnlk/a2o4UlBwS25PR2V3/NkpoaEJlZVlLWnFR/RmRiVzZKZ2hfZDJV/R2lVZGRoc0NoLW51/eWpGV01LX2Y5VkJY/Tm02RDhHRHJXL3M4/NzYvc2VyaWUlMjBh/JTIwbmV3JTIwbG9n/byUyMCg1KS5qcGc" alt="Serie A" loading="lazy" className="w-10 h-10 rounded-md object-contain" />
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
                            <img src="https://imgs.search.brave.com/B-aLd18fXL1FI-BfIjqhVuqymX1n17oBfawGR_iaqG0/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9sb2dv/ZG93bmxvYWQub3Jn/L3dwLWNvbnRlbnQv/dXBsb2Fkcy8yMDE5/LzA5L2xpZ3VlLTEt/bG9nby0yLnBuZw" alt="Ligue 1" loading="lazy" className="w-10 h-10 rounded-md object-contain" />
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
                            <img src="https://imgs.search.brave.com/VM8SPUcbUGofqFgywsUpr6cSg-0fakvglzpGDCyMQQw/rs:fit:500:0:1:0/g:ce/aHR0cHM6Ly9ibG9n/Z2VyLmdvb2dsZXVz/ZXJjb250ZW50LmNv/bS9pbWcvYi9SMjl2/WjJ4bC9BVnZYc0Vn/cWp6TnBfamYtc0RF/YU9GM3lpMXpRUlJo/eU1tYnd6VlpkM0Rl/TUV2R2NIR3gwdmxX/SlZYWUhFWlR6ZDlK/S1pZdThGc21QeTBu/dkdiS3Y0WjlKUVRF/eGYyMkNaeVE1eGtS/S0JPUGtRZ3JoQS1Y/NmEwOEZhX2hwVjZh/d2hyZnlXaTlNS2dk/dl9FY2NHSUJkL3Mx/MDAwLzIwMjEtMjIt/dWVmYS1jaGFtcGlv/bnMtbGVhZ3VlLWxv/Z28rJTI4MSUyOS5w/bmc" alt="Champions League" loading="lazy" className="w-10 h-10 rounded-md object-contain" />
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
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        {children}
      </main>
    </div>
  )
}
