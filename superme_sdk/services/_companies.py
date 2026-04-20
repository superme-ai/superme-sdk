"""Company and role listing methods."""

from __future__ import annotations


class CompaniesMixin:

    def list_companies(self, *, active_only: bool = True) -> list[dict]:
        """List companies with active roles.

        Example:
            ```python
            companies = client.list_companies()
            for c in companies:
                print(c["name"], c["company_id"])
            ```

        Returns:
            List of company dicts with ``company_id``.
        """
        result = self._mcp_tool_call("list_companies", {"active_only": active_only})
        companies = result.get("companies", [])
        return companies if isinstance(companies, list) else []

    def list_company_roles(self, company_id: str) -> list[dict]:
        """List active roles for a company.

        Example:
            ```python
            roles = client.list_company_roles("company_abc123")
            for r in roles:
                print(r["title"], r["location"])
            ```

        Returns:
            List of role dicts (id, title, summary, location, etc.).
        """
        result = self._mcp_tool_call(
            "get_company_roles", {"company_id": company_id}
        )
        roles = result.get("roles", [])
        return roles if isinstance(roles, list) else []

    def list_active_roles(self, *, limit: int = 10) -> list[dict]:
        """List active roles across all companies.

        Example:
            ```python
            roles = client.list_active_roles(limit=5)
            for r in roles:
                print(r["title"], r["company_name"])
            ```

        Fetches companies first, then collects roles up to *limit*.

        Returns:
            List of role dicts.
        """
        companies = self.list_companies(active_only=True)
        all_roles: list[dict] = []
        for company in companies:
            cid = company.get("company_id")
            if not cid:
                continue
            roles = self.list_company_roles(cid)
            all_roles.extend(roles)
            if len(all_roles) >= limit:
                break
        return all_roles[:limit]
