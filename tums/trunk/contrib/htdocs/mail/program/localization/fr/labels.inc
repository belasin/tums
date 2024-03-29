<?php

/*
 +-----------------------------------------------------------------------+
 | language/fr/labels.inc                                                |
 |                                                                       |
 | Language file of the RoundCube Webmail client                         |
 | Copyright (C) 2005, RoundQube Dev. - Switzerland                      |
 | Licensed under the GNU GPL                                            |
 |                                                                       |
 +-----------------------------------------------------------------------+
 | Author: aldweb <info@aldweb.com>, Pierre HAEGELI <pierre@haegeli.net> |
 +-----------------------------------------------------------------------+

 $Id: labels.inc 220 2006-06-12 17:33:21Z roundcube $

*/

$labels = array();

// login page
$labels['welcome']   = 'Bienvenue à $product';
$labels['username']  = 'ID utilisateur';
$labels['password']  = 'Mot de passe';
$labels['server']    = 'Serveur';
$labels['login']     = 'Connexion';

// taskbar
$labels['logout']   = 'Quitter';
$labels['mail']     = 'e-Mail';
$labels['settings'] = 'Préférences';
$labels['addressbook'] = 'Carnet d\'adresses';

// mailbox names
$labels['inbox']  = 'Boîte de réception';
$labels['sent']   = 'Messages envoyés';
$labels['trash']  = 'Corbeille';
$labels['drafts'] = 'Brouillons';
$labels['junk']   = 'A trier';

// message listing
$labels['subject'] = 'Objet';
$labels['from']    = 'De';
$labels['to']      = 'A';
$labels['cc']      = 'Cc';
$labels['bcc']     = 'Cci';
$labels['replyto'] = 'Répondre à';
$labels['date']    = 'Date';
$labels['size']    = 'Taille';
$labels['priority'] = 'Priorité';
$labels['organization'] = 'Organisation';

// aliases
$labels['reply-to'] = $labels['replyto'];

$labels['mailboxlist'] = 'Dossiers';
$labels['messagesfromto'] = 'Messages $from à $to sur $count';
$labels['messagenrof'] = 'Message $nr sur $count';

$labels['moveto']   = 'Déplacer vers...';
$labels['download'] = 'Télécharger';

$labels['filename'] = 'Nom du fichier';
$labels['filesize'] = 'Taille du fichier';

$labels['preferhtml'] = 'Préférer HTML';
$labels['htmlmessage'] = 'Message HTML';
$labels['prettydate'] = 'Affichage réduit des dates';

$labels['addtoaddressbook'] = 'Ajouter au carnet d\'adresses';

// weekdays short
$labels['sun'] = 'Dim';
$labels['mon'] = 'Lun';
$labels['tue'] = 'Mar';
$labels['wed'] = 'Mer';
$labels['thu'] = 'Jeu';
$labels['fri'] = 'Ven';
$labels['sat'] = 'Sam';

// weekdays long
$labels['sunday']    = 'Dimanche';
$labels['monday']    = 'Lundi';
$labels['tuesday']   = 'Mardi';
$labels['wednesday'] = 'Mercredi';
$labels['thursday']  = 'Jeudi';
$labels['friday']    = 'Vendredi';
$labels['saturday']  = 'Samedi';

$labels['today'] = 'Aujourd\'hui';

// toolbar buttons
$labels['checkmail'] = 'Vérification des nouveaux messages';
$labels['writenewmessage']  = 'Créer un nouveau message';
$labels['replytomessage']   = 'Répondre au message';
$labels['replytoallmessage'] = 'Répondre à tous';
$labels['forwardmessage']   = 'Transmettre le message';
$labels['deletemessage']    = 'Déplacer le message dans la corbeille';
$labels['printmessage']     = 'Imprimer ce message';
$labels['previousmessages'] = 'Voir les messages précédents';
$labels['nextmessages']     = 'Voir les messages suivants';
$labels['backtolist']       = 'Retourner à la liste des messages';
$labels['viewsource']       = 'Voir le code source';

$labels['select'] = 'Sélectionner';
$labels['all'] = 'Tous';
$labels['none'] = 'Aucun';
$labels['unread'] = 'Non lus';

//$labels['compact'] = 'Compresser';
$labels['empty'] = 'Vider';
$labels['purge'] = 'Purger';

$labels['quota'] = 'Utilisation Disque';
$labels['unknown'] = 'inconnue';
$labels['unlimited'] = 'illimitée';

$labels['quicksearch']  = 'Recherche rapide';
$labels['resetsearch']  = 'Réinitialiser la recherche';


// message compose
$labels['compose']  = 'Composer un nouveau message';
$labels['savemessage']  = 'Sauvegarder ce brouillon';
$labels['sendmessage']  = 'Envoyer le message maintenant';
$labels['addattachment']  = 'Joindre un fichier';
$labels['charset']  = 'Encodage';
$labels['returnreceipt'] = 'Accusé de réception';

$labels['checkspelling'] = 'Vérifier l\'orthographe';
$labels['resumeediting'] = 'Retourner à l\'édition';
$labels['revertto'] = 'Revenir à';

$labels['attachments'] = 'Fichiers joints';
$labels['upload'] = 'Joindre';
$labels['close']  = 'Fermer';

$labels['low']     = 'Basse';
$labels['lowest']  = 'La plus basse';
$labels['normal']  = 'Normale';
$labels['high']    = 'Elevée';
$labels['highest'] = 'La plus élevée';

$labels['nosubject']  = '(pas de sujet)';
$labels['showimages'] = 'Montrer les images';


// address boook
$labels['name']      = 'Nom à afficher';
$labels['firstname'] = 'Prénom';
$labels['surname']   = 'Nom';
$labels['email']     = 'e-Mail';

$labels['addcontact'] = 'Ajouter un nouveau contact';
$labels['editcontact'] = 'Editer le contact';

$labels['edit']   = 'Editer';
$labels['cancel'] = 'Annuler';
$labels['save']   = 'Sauvegarder';
$labels['delete'] = 'Supprimer';

$labels['newcontact']     = 'Créer un nouveau contact';
$labels['addcontact']     = 'Ajouter le contact sélectionné à votre Carnet d\'adresses';
$labels['deletecontact']  = 'Supprimer les contacts sélectionnés';
$labels['composeto']      = 'Ecrire un message à';
$labels['contactsfromto'] = 'Contacts $from à $to sur $count';
$labels['print']          = 'Imprimer';
$labels['export']         = 'Exporter';

$labels['previouspage'] = 'Montrer page précédente';
$labels['nextpage']     = 'Montrer page suivante';


// LDAP search
$labels['ldapsearch'] = 'Recherche dans répertoires LDAP';

$labels['ldappublicsearchname']    = 'Nom du contact';
$labels['ldappublicsearchtype'] = 'Correspondance exacte ?';
$labels['ldappublicserverselect'] = 'Sélectionnez les serveurs';
$labels['ldappublicsearchfield'] = 'Recherche sur';
$labels['ldappublicsearchform'] = 'Chercher un contact';
$labels['ldappublicsearch'] = 'Recherche';


// settings
$labels['settingsfor']  = 'Paramètres pour';

$labels['preferences']  = 'Préférences';
$labels['userpreferences']  = 'Préférences utilisateur';
$labels['editpreferences']  = 'Editer les préférences utilisateur';

$labels['identities']  = 'Identités';
$labels['manageidentities']  = 'Gérer les identités pour ce compte';
$labels['newidentity']  = 'Nouvelle identité';

$labels['newitem']  = 'Nouvel élément';
$labels['edititem']  = 'Editer l\'élément';

$labels['setdefault']  = 'Paramètres par défaut';
$labels['language']  = 'Langue';
$labels['timezone']  = 'Fuseau horaire';
$labels['pagesize']  = 'Nombre de lignes par page';
$labels['signature'] = 'Signature';
$labels['dstactive'] = 'Heure d\'été';

$labels['folder']  = 'Dossier';
$labels['folders']  = 'Dossiers';
$labels['foldername']  = 'Nom du dossier';
$labels['subscribed']  = 'Abonné';
$labels['create']  = 'Créer';
$labels['createfolder']  = 'Créer un nouveau dossier';
$labels['rename'] = 'Renommer';
$labels['renamefolder'] = 'Renommer le dossier';
$labels['deletefolder']  = 'Supprimer le dossier';
$labels['managefolders']  = 'Gérer les dossiers';

$labels['sortby'] = 'Trier par';
$labels['sortasc']  = 'Tri ascendant';
$labels['sortdesc'] = 'Tri descendant';

?>
