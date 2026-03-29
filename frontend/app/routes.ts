import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("search", "routes/search.tsx"),
  route("feed", "routes/feed.tsx"),
  route("bookmarks", "routes/bookmarks.tsx"),
  route("login", "routes/login.tsx"),
  route("register", "routes/register.tsx"),
  route("paper/:id", "routes/paper.$id.tsx"),
] satisfies RouteConfig;
