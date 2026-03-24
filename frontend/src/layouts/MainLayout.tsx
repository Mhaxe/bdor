import * as React from "react"
import { MenuIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from "@/components/ui/navigation-menu"
// Use plain anchors here to avoid requiring a Router context when the
// component is rendered outside of the SPA root (server-side pages, previews, etc.).

type Props = {
  children: React.ReactNode
}

const competitions = [
  {
    name: "Premier League",
    imageSrc: "/static/competitions/premier-league.webp",
    imageAlt: "Premier League",
  },
  {
    name: "La Liga",
    imageSrc: "/static/competitions/la-liga.webp",
    imageAlt: "La Liga",
  },
  {
    name: "Bundesliga",
    imageSrc: "/static/competitions/bundesliga.webp",
    imageAlt: "Bundesliga",
  },
  {
    name: "Serie A",
    imageSrc: "/static/competitions/serie-a.webp",
    imageAlt: "Serie A",
  },
  {
    name: "Ligue 1",
    imageSrc: "/static/competitions/ligue-1.webp",
    imageAlt: "Ligue 1",
  },
  {
    name: "Champions League",
    imageSrc: "/static/competitions/champions-league.webp",
    imageAlt: "Champions League",
  },
  {
    name: "Europa League",
    imageSrc: "/static/competitions/europa-league.webp",
    imageAlt: "Europa League",
  },
] as const

export default function MainLayout({ children }: Props) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="w-full border-b bg-background/50">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
          <div className="flex min-w-0 items-center gap-4 md:gap-6">
            <a href="#" onClick={(e) => e.preventDefault()} className="flex items-center gap-3" aria-disabled>
              <img src="/static/balonrank-logo.png" alt="BalonRank logo" className="h-12 w-auto object-contain" />
              <span className="font-semibold text-sm">BalonRank</span>
            </a>
            <NavigationMenu className="hidden flex-none md:flex">
              <NavigationMenuList className="flex-none justify-start">
              <NavigationMenuItem>
                <NavigationMenuTrigger>Supported Competitions</NavigationMenuTrigger>
                <NavigationMenuContent>
                  <ul className="grid w-[400px] gap-2 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
                    {competitions.map((competition) => (
                      <li key={competition.name}>
                        <NavigationMenuLink asChild>
                          <a href="#" onClick={(e) => e.preventDefault()}>
                            <div className="flex items-center gap-3">
                              <img
                                src={competition.imageSrc}
                                alt={competition.imageAlt}
                                loading="lazy"
                                className="size-10 rounded-md object-contain"
                              />
                              <div className="flex flex-col gap-1 text-sm">
                                <div className="leading-none font-medium">{competition.name}</div>
                              </div>
                            </div>
                          </a>
                        </NavigationMenuLink>
                      </li>
                    ))}
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

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="md:hidden"
                aria-label="Open navigation menu"
              >
                <MenuIcon />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-72 md:hidden">
              <DropdownMenuLabel>Supported Competitions</DropdownMenuLabel>
              <DropdownMenuGroup>
                {competitions.map((competition) => (
                  <DropdownMenuItem key={competition.name} asChild>
                    <a
                      href="#"
                      onClick={(e) => e.preventDefault()}
                      className="flex items-center gap-3"
                    >
                      <img
                        src={competition.imageSrc}
                        alt={competition.imageAlt}
                        loading="lazy"
                        className="size-8 rounded-md object-contain"
                      />
                      <span>{competition.name}</span>
                    </a>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>FAQs</DropdownMenuLabel>
              <DropdownMenuGroup>
                <DropdownMenuItem asChild>
                  <a href="#" onClick={(e) => e.preventDefault()}>
                    How are the points calculated?
                  </a>
                </DropdownMenuItem>
              </DropdownMenuGroup>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        {children}
      </main>
    </div>
  )
}
