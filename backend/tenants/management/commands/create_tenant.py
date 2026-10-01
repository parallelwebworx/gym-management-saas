"""
create_tenant — provision a new gym atomically.

Mirrors the source app's ``scripts/create-tenant.ts``: there is NO public signup,
so tenants and staff are created out-of-band by an operator. Three modes:

  # New gym + "Main Branch" + owner user (default)
  python manage.py create_tenant --gym "Iron Paradise" \
      --owner-email owner@example.com --owner-password 's3cret' \
      --owner-name "Asha Rao"

  # Add a staff user to an existing gym
  python manage.py create_tenant --mode staff --gym-id 1 \
      --email front@example.com --password 's3cret' \
      --role receptionist --branch-id 1

  # Add a branch to an existing gym
  python manage.py create_tenant --mode branch --gym-id 1 --branch "MG Road"

Passwords may be passed via --*-password; if omitted the command prompts (hidden)
so they never land in shell history.
"""
from getpass import getpass

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tenants.models import Branch, Gym, Role, User


class Command(BaseCommand):
    help = "Provision a gym tenant, staff user, or branch (no public signup)."

    def add_arguments(self, parser):
        parser.add_argument("--mode", choices=["gym", "staff", "branch"], default="gym")
        # gym mode
        parser.add_argument("--gym")
        parser.add_argument("--owner-email")
        parser.add_argument("--owner-password")
        parser.add_argument("--owner-name", default="")
        parser.add_argument("--main-branch", default="Main Branch")
        # staff / branch modes
        parser.add_argument("--gym-id", type=int)
        parser.add_argument("--email")
        parser.add_argument("--password")
        parser.add_argument("--name", default="")
        parser.add_argument(
            "--role",
            choices=[Role.OWNER, Role.BRANCH_MANAGER, Role.RECEPTIONIST],
            default=Role.RECEPTIONIST,
        )
        parser.add_argument("--branch-id", type=int)
        parser.add_argument("--branch")

    def handle(self, *args, **opts):
        mode = opts["mode"]
        if mode == "gym":
            self._create_gym(opts)
        elif mode == "staff":
            self._create_staff(opts)
        elif mode == "branch":
            self._create_branch(opts)

    # -- gym ---------------------------------------------------------------
    def _create_gym(self, opts):
        gym_name = opts.get("gym")
        email = opts.get("owner_email")
        if not gym_name or not email:
            raise CommandError("--gym and --owner-email are required in gym mode.")
        password = opts.get("owner_password") or getpass("Owner password: ")
        if not password:
            raise CommandError("An owner password is required.")

        email = email.strip().lower()
        if User.objects.filter(email=email).exists():
            raise CommandError(f"A user with email {email} already exists.")

        with transaction.atomic():
            gym = Gym.objects.create(name=gym_name)
            branch = Branch.objects.create(gym=gym, name=opts["main_branch"])
            owner = User.objects.create_user(
                email=email,
                password=password,
                full_name=opts.get("owner_name", ""),
                role=Role.OWNER,
                gym=gym,
                branch=branch,
            )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created gym #{gym.id} '{gym.name}', branch #{branch.id} "
                f"'{branch.name}', owner #{owner.id} <{owner.email}>."
            )
        )

    # -- staff -------------------------------------------------------------
    def _create_staff(self, opts):
        gym_id = opts.get("gym_id")
        email = opts.get("email")
        if not gym_id or not email:
            raise CommandError("--gym-id and --email are required in staff mode.")
        password = opts.get("password") or getpass("Password: ")
        if not password:
            raise CommandError("A password is required.")

        gym = self._get_gym(gym_id)
        branch = None
        if opts.get("branch_id"):
            branch = self._get_branch(gym, opts["branch_id"])

        email = email.strip().lower()
        if User.objects.filter(email=email).exists():
            raise CommandError(f"A user with email {email} already exists.")

        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=opts.get("name", ""),
            role=opts["role"],
            gym=gym,
            branch=branch,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {user.role} #{user.id} <{user.email}> in gym #{gym.id}."
            )
        )

    # -- branch ------------------------------------------------------------
    def _create_branch(self, opts):
        gym_id = opts.get("gym_id")
        name = opts.get("branch")
        if not gym_id or not name:
            raise CommandError("--gym-id and --branch are required in branch mode.")
        gym = self._get_gym(gym_id)
        branch = Branch.objects.create(gym=gym, name=name)
        self.stdout.write(
            self.style.SUCCESS(f"Created branch #{branch.id} '{branch.name}' in gym #{gym.id}.")
        )

    # -- helpers -----------------------------------------------------------
    def _get_gym(self, gym_id):
        gym = Gym.objects.filter(id=gym_id, deleted_at__isnull=True).first()
        if not gym:
            raise CommandError(f"No gym with id {gym_id}.")
        return gym

    def _get_branch(self, gym, branch_id):
        branch = Branch.objects.filter(
            id=branch_id, gym=gym, deleted_at__isnull=True
        ).first()
        if not branch:
            raise CommandError(f"No branch #{branch_id} in gym #{gym.id}.")
        return branch
