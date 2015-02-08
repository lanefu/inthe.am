import uuid

from django.contrib.auth.models import User
from django.db import models


class KanbanMembershipManager(models.Manager):
    def active(self):
        return super(KanbanMembershipManager, self).get_queryset().filter(
            valid=True,
            accepted=True,
        )

    def pending(self):
        return super(KanbanMembershipManager, self).get_queryset().filter(
            valid=True,
            accepted=False,
        )

    def owners_of(self, kanban_board):
        return self.active().filter(
            role=KanbanMembership.OWNER,
            kanban_board=kanban_board,
        )

    def members_of(self, kanban_board):
        return self.active().filter(
            kanban_board=kanban_board
        )

    def user_is_member(self, kanban_board, user):
        return self.members_of(kanban_board).filter(
            member=user
        ).exists()

    def user_is_owner(self, kanban_board, user):
        return self.owners_of(kanban_board).filter(
            member=user
        ).exists()


class KanbanMembership(models.Model):
    OWNER = 'owner'
    MEMBER = 'member'

    ROLES = (
        (OWNER, 'Owner', ),
        (MEMBER, 'Member', ),
    )

    uuid = models.CharField(
        max_length=36,
        db_index=True,
    )
    kanban_board = models.ForeignKey(
        'KanbanBoard',
        related_name='memberships',
        db_index=True,
    )
    sender = models.ForeignKey(
        User,
        related_name='sent_memberships',
    )
    member = models.ForeignKey(
        User,
        related_name='kanban_memberships',
        null=True,
        blank=True,
        db_index=True,
    )
    invitee_email = models.EmailField(
        max_length=254,
        db_index=True,
    )
    role = models.CharField(
        max_length=255,
        choices=ROLES,
        default=MEMBER
    )
    accepted = models.BooleanField(default=False)
    valid = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True)

    objects = KanbanMembershipManager()

    def reject(self):
        self.valid = False
        self.accepted = False

    def accept(self):
        self.valid = True
        self.accepted = True

    @property
    def invitee(self):
        User.objects.get(email=self.invitee_email)

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        super(KanbanMembership, self).save(*args, **kwargs)

    def __unicode__(self):
        if self.valid and self.accepted:
            return "%s level membership to %s by %s" % (
                self.role,
                self.kanban_board,
                self.member,
            )
        elif self.valid and not self.accepted:
            return "(Pending Invitation) %s level membership to %s by %s" % (
                self.role,
                self.kanban_board,
                self.member,
            )
        elif not self.valid:
            return "(Rejected Invitation) %s level membership to %s by %s" % (
                self.role,
                self.kanban_board,
                self.member,
            )

    class Meta:
        app_label = 'taskmanager'
