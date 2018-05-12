
# Users section
usersBeginInstruction = "Please select a user from the list on the left"
userManagement = " User Management"
userFormLabelUsername = "Username (required)"
userFormLabelName = "First Name (required)"
userFormLabelPass = "Password"
userFormLabelForward = "Forward mail to"
userFormLabelAddline = "Add line"
userFormLabelAlias = "Email aliases"
userFormLabelVacationActive = "Vacation note active"
userFormTextVacationNote = "Tick this to enable/disable the vacation note."
userFormLabelVacation = "Vacation"
userFormLabelWeb = "Web Proxy Access"
userFormLabelAdmin = "TUMS Admin"
userFormLabelEmail = "Email Enabled"
userFormLabelReports = "Reports Access"
userFormLabelCopy = "Copy mail to"
userFormTextCopy = "Copy all mail sent to this address to another address. Please note this may be subject to legislation in your region."
userFormLabelVPN = "VPN Access"
userFormLabelFTP = "FTP access"
userFormLabelGlobalFTP = "Global FTP access"
userFormTextVPN = "Creates Vulani VPN access for this user and emails them the details"
userFormTextFTP = "Allows this user to FTP and login localy to the server"
userFormTextGlobal = "Allows this user to access the entire filesystem from FTP (not recommended!)"
userFormLabelEmailAddress = "EMail Address"
userFormLabelSurname = "Surname"
userFormLabelDomainName = "Domain name"
userFormGroupName = "Group Name"

userMailWelcomeMessage = "Welcome to your new account, %s"

userTabSettings = "User Settings"
userTabPermissions = "User Permissions"
userTabMail = "Mail Settings"
userTabAccess = "Access Permissions"

userHeadingAddUser = "Add user to "
userHeadingEditUser = "Edit user "
userHeadingAddGroup = "Add new group"
userHeadingAddDomain = "Add domain"
userHeadingMemberships = "Group memberships for group "
userHeadingMembershipsUser = "Group memberships for "

userLinkCreateGroup = "Create new group"
userLinkEditMembership = "Edit Memberships"
userLinkDeleteUser = " Delete this user"

userConfirmDelete = "Are you sure you want to delete this user?"

userWarningEditRoot = "You are editing the actual root user. Please be very careful here."
userErrorDomainPermission = "You do not have permission to add domains"
userErrorUserPlayedWithLink = " * Tums casts Domain Prediction Level 99 [AKA: Why did you mess with the URL?]"

# Tools Menu
tools = "Tools"
toolsInstruction = "Please make a selection from the menu on the left."

toolsMenuVPN                    = "VPN Configuration"
toolsMenuVPNTooltip             = "Configure VPN Connections"
toolsMenuNetdrive               = "Network Drives"
toolsMenuNetdriveTooltip        = "Configure Network Drive Mappings"
toolsMenuFileShares             = "File Shares"
toolsMenuFileSharesTooltip      = "Configure SMB File Shares"
toolsMenuDomainSetup            = "Domain Setup"
toolsMenuDomainSetupTooltip     = "Configure SMB Domain"
toolsMenuDomainGroups           = "Domain Groups"
toolsMenuDomainGroupsTooltip    = "Domain membership matrix"
toolsMenuWebProxy               = "Web Proxy"
toolsMenuWebProxyTooltip        = "Web proxy access configuration settings"
toolsMenuDHCP                   = "DHCP Configuration"
toolsMenuDHCPTooltip            = "DHCP configuration settings"
toolsMenuComputers              = "Domain Computers"
toolsMenuComputersTooltip       = "Computers joined to this domain"
toolsMenuNetconf                = "Network Configuration"
toolsMenuNetconfTooltip         = "Network interface configuration and policies"
toolsMenuPPP                    = "PPP Configuration"
toolsMenuPPPTooltip             = "Start, stop, create and delete PPP interfaces"
toolsMenuProfiles               = "Profiles"
toolsMenuProfilesTooltip        = "Manage configuration profiles"
toolsMenuFirewall               = "Firewall"
toolsMenuFirewallTooltip        = "Network firewall configuration"
toolsMenuQOS                    = "QOS Management"
toolsMenuQOSTooltip             = "Quality Of Service management. Proritise different internet service traffic"
toolsMenuPolicy                 = "System Policy"
toolsMenuPolicyTooltip          = "System policy control. P2P blocking and other settings"
toolsMenuBackups                = "Backups"
toolsMenuBackupsTooltip         = "Automated and manual system backups"
toolsMenuBrowser                = "File Browser"
toolsMenuBrowserTooltip         = "A simple file browser for the local filesystem"
toolsMenuMail                   = "Mail Configuration"
toolsMenuMailTooltip            = "Mail server configuration."

# Backup

backupPath = "Backup Path"
backupPathDescription = "Paths to backup, separated by a semicolon."
backupDestination = "Backup Destination"
backupDestinationDescription = "Folder on backup device where files are backed up to (This must exist first)"
backupNotify = "Notify address"
backupNotifyDescription = "Email address of persons who will be notified once backup has been completed, separated by semicolon"
backupDrive = "Backup device"
backupSchedule = "Schedule Backup"
backupTime = "Backup time"
backupConfirmDelete = "Are you sure you want to delete this backup process?"

backupSet = " Backup Sets"
backupHeaderDescription = "Description"
backupHeaderNotify = "Notify"
backupHeaderDevice = "Device"
backupHeaderSource = "Source Path(s)" 
backupHeaderDestination = "Destination Path"
backupHeaderAutomated = "Automated"

backupCreateSet = "Create a backup set"

# VPN

vpnLabelWindows = "Windows Server"
vpnDescripWindows = "Enable Windows VPN Support"
vpnLabelWinserver = "Server IP Address"
vpnLabelExtwinserver = "External IP Address"
vpnDescripExtwinserver = "The external IP address of the windows server (if you are unsure, leave this blank)"
vpnLabelOpenvpn = "Vulani VPN" 
vpnDescripOpenvpn = "Enable Vulani VPN"
vpnRangeStart = "IP Range"
vpnRangeTo = " to "
vpnMTU = "MTU"
vpnWINSServer = "WINS Server"
vpnDNSServer = "DNS Server"
vpnDomain = "Domain"
vpnRoutesPush = "Routes to push"
vpnName = "Name"
vpnMail = "EMail"
vpnStaticIP = "Static IP (blank for dynamic allocation)"
vpnMailQuestion  = "EMail key to user?"
vpnConfigDetails = "VPN Configuration Details"
vpnConfig = "VPN Configuration"
vpnTabWindows = "Windows VPN"
vpnTabTCS = "Vulani VPN"
vpnTabUsers = "Vulani VPN Users"
vpnHeadingWindows = "Windows VPN"
vpnHeadingTCS = vpnTabTCS
vpnHeadingTCSUsers = vpnTabUsers
vpnHeadingAddUser = "Add VPN user"
vpnCertificateName = "Certificate Name"
vpnConfirmRevoke = "Are you sure you want to revoke this vpn key?"

# Computers

compName = "Computer Name"
compConfirm = "Are you sure you want to delete this computer trust account?"
compHeading = " Computer trust management"
compHeadingList = "Current domain members"
compHeadingAdd = "Add Computer"

# Mail Settings

eximBlacklistEntry = "Blacklist Entry"
eximWhitelistEntry = "Whitelist Entry"
eximHubbedHostMappings = "Hubbed host mappings"
eximHubbedHostDescription = "Domains listed here have their mail redirected to a different SMTP server specified on the same line"
eximLocalDomains = "Local delivery domains"
eximLocalDescription = "Domains listed here are directly accepted by this server. They should rather be controlled by the Users section"
eximRelayDomains = "Relay domains"
eximRelayDescription = "Destination domains which we will accept anonymous relay for (This is most often for backup mail servers)"
eximMaxMailSize = "Maximum mail size"
eximMaxSizeDescription = "The maximum size of a mail, with base64 encoding, plus it's attatchments, which will be allowed through this server. Leave blank to allow any mail through"
eximBlockedAttachment = "Blocked attachment extensions"
eximBlockedDescription = "Extensions of files which are blocked by this server. Sepparate multiple entries with a comma."
eximBlockedMovies = "Block movies and audio"
eximBlockedMovieDescription = "A quick shortcut for blocking all movie and audio files"
eximBlockHarmful = "Block harmfull files"
eximBlockHarmfulDescription = "A quick shortcut for blocking harmfull extensions such as executable files"
eximGreylisting = "Greylisting"
eximGreylistingDescription = "Enable greylisting (delays mail acceptance to decrease spam)"
eximSpamScore = "Spam Score"
eximSpamScoreDescription = "Maximum spam score after which mail will be blocked (Default: 70)"
eximSMTPRelay = "SMTP Relay"
eximSMTPRelayDescription = "SMTP server to relay mail to instead of trying to deliver it directly"
eximMailCopy = "Mail copy"
eximMailCopyDescription = "Copy all mails to this address. Please note this may be subject to legislation in your region."
eximConfirmDelete = "Are you sure you want to delete this entry?"
eximTabMail = "Mail Settings"
eximTabRelay = "Relay Domains"
eximTabHubbed = "Hubbed Domains"
eximTabLocal = "Local Domains"
eximTabBlocked = "Blacklist"
eximTabWhitelist = "Whitelist"
eximAddWhitelist = "Add to whitelist"
eximAddrOrHost = "Address or Host"
eximAddr = "Address"
eximAddBlacklist = "Add to blacklist"

profileSource = "Source profile"
profileDest = "New name"