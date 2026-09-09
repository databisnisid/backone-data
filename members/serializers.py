import os
from rest_framework import serializers
from .models import Members, MemberLink, Links, SdwanPackage, BaaStatus, LinkRole
from .rbac import writable_fields, readable_fields, CORE_EDIT_FIELDS


class MemberLinkSerializer(serializers.ModelSerializer):
    member = serializers.PrimaryKeyRelatedField(
        queryset=Members.objects.all(), write_only=True, required=False
    )
    role = serializers.SlugRelatedField(
        slug_field="name", queryset=LinkRole.objects.all(), required=False, allow_null=True
    )
    service = serializers.PrimaryKeyRelatedField(
        queryset=Links.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = MemberLink
        fields = ("id", "member", "role", "service", "provider", "capacity", "sid")


class MemberSerializer(serializers.ModelSerializer):
    member_links = MemberLinkSerializer(many=True, read_only=True)
    network_name = serializers.CharField(source="network.name", read_only=True)
    network_group = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    links = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    sdwan_package = serializers.SlugRelatedField(
        slug_field="name",
        queryset=SdwanPackage.objects.all(),
        required=False,
        allow_null=True,
    )
    baa_status_category = serializers.SlugRelatedField(
        slug_field="name",
        queryset=BaaStatus.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Members
        fields = (
            "id",
            "name",
            "member_code",
            "member_id",
            "address",
            "location",
            "online_at",
            "offline_at",
            "network",
            "network_name",
            "network_group",
            "links",
            "member_links",
            "service_line",
            "quota_string",
            "upload_baa",
            "invoice_number",
            "invoice_file",
            "po_file_user",
            "po_file_vendor",
            "bap_file",
            "ip_address",
            "sdwan_package",
            "project_number",
            "baa_status_category",
            "notes",
            "is_manual",
            "is_online",
        )
        read_only_fields = ("is_manual",)

    def get_network_group(self, obj):
        return obj.network_group()

    def get_is_online(self, obj):
        if obj.offline_at is None:
            return 1
        from django.utils import timezone
        return 1 if obj.offline_at >= timezone.now() else 0

    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.context.get("request").user if self.context.get("request") else None
        allowed = readable_fields(user) if user else set(self.Meta.fields)
        for name in list(data.keys()):
            if name not in allowed:
                data.pop(name, None)
        return data

    def _assert_writable(self, validated_data):
        user = self.context.get("request").user if self.context.get("request") else None
        if user is None:
            return
        allowed = writable_fields(user)
        denied = [f for f in validated_data if f not in allowed]
        if denied:
            raise serializers.ValidationError(
                {"detail": "Role lacks write permission for field(s): %s" % ", ".join(denied)}
            )

    def update(self, instance, validated_data):
        self._assert_writable(validated_data)
        if not instance.is_manual:
            denied_core = [f for f in validated_data if f in CORE_EDIT_FIELDS]
            if denied_core:
                raise serializers.ValidationError(
                    {"detail": "Synced (upstream) sites: core fields read-only — %s" % ", ".join(denied_core)}
                )
        return super().update(instance, validated_data)

    def create(self, validated_data):
        self._assert_writable(validated_data)
        return super().create(validated_data)


ALLOWED_UPLOAD_EXT = (".pdf", ".xls", ".xlsx", ".doc", ".docx")
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


class MemberFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Members
        fields = ("upload_baa", "po_file_user", "po_file_vendor", "invoice_file", "bap_file")
        extra_kwargs = {
            "upload_baa": {"required": False},
            "po_file_user": {"required": False},
            "po_file_vendor": {"required": False},
            "invoice_file": {"required": False},
            "bap_file": {"required": False},
        }

    def validate(self, attrs):
        for name, file_obj in attrs.items():
            ext = os.path.splitext(file_obj.name)[1].lower()
            if ext not in ALLOWED_UPLOAD_EXT:
                raise serializers.ValidationError(
                    {"detail": "%s: unsupported file type '%s'" % (name, ext)}
                )
            if file_obj.size > MAX_UPLOAD_SIZE:
                raise serializers.ValidationError(
                    {"detail": "%s: file exceeds %d MB limit" % (name, MAX_UPLOAD_SIZE // (1024 * 1024))}
                )
        return attrs

    def _assert_writable(self, validated_data):
        user = self.context.get("request").user if self.context.get("request") else None
        if user is not None:
            allowed = writable_fields(user)
            denied = [f for f in validated_data if f not in allowed]
            if denied:
                raise serializers.ValidationError(
                    {"detail": "Role lacks write permission for field(s): %s" % ", ".join(denied)}
                )

    def update(self, instance, validated_data):
        self._assert_writable(validated_data)
        return super().update(instance, validated_data)
