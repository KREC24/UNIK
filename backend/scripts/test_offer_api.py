import sys, asyncio
sys.path.insert(0, 'K:/Projects/UNIK/backend')

async def test():
    from app.core.database import session_factory
    from app.services.offer_service import generate_offer_pdf
    from sqlalchemy import select
    from app.models.database import Project
    import uuid

    async with session_factory() as s:
        pid = uuid.UUID('3625e7ed-0e5a-4fef-b985-176ac3b8a538')
        r = await s.execute(select(Project).where(Project.id == pid))
        p = r.scalar_one_or_none()
        print(f'Project: {p.name}' if p else 'NOT FOUND')

        from app.api.routes.offers import build_offer_from_project
        items = []
        if p and p.line_items:
            for li in p.line_items:
                items.append({'name': f'{li.type_name} {li.mark}'.strip()})

        pdf = generate_offer_pdf(
            object_name=p.name if p else 'Test',
            items=items,
        )
        print(f'PDF: {len(pdf)} bytes')
        with open('K:/Projects/UNIK/output/api_kp2.pdf', 'wb') as f:
            f.write(pdf)

asyncio.run(test())
