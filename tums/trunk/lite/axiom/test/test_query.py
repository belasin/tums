
import operator, random

from twisted.trial.unittest import TestCase

from axiom.iaxiom import IComparison, IColumn
from axiom.store import Store, ItemQuery
from axiom.item import Item, Placeholder

from axiom import errors
from axiom.attributes import reference, text, bytes, integer, AND, OR

class A(Item):
    schemaVersion = 1
    typeName = 'a'

    reftoc = reference()
    type = text(indexed=True)


class B(Item):
    schemaVersion = 1
    typeName = 'b'

    cref = reference()
    name = text(indexed=True)

class C(Item):
    schemaVersion = 1
    typeName = 'c'

    name = text(indexed=True)

class D(Item):
    schemaVersion = 1
    typeName = 'd'
    id = bytes()
    one = bytes()
    two = bytes()
    three = bytes()
    four = text()

class E(Item):
    schemaVersion = 1
    typeName = 'e'
    name = text()
    transaction = text()
    amount = integer()


class ThingWithCharacterAndByteStrings(Item):
    schemaVersion = 1

    typeName = 'ThingWithCharacterAndByteStrings'

    characterString = text(caseSensitive=True)
    caseInsensitiveCharString = text(caseSensitive=False)

    byteString = bytes()


class BasicQuery(TestCase):

    def test_rightHandStoreIDComparison(self):
        """
        Test that a StoreID column on the right-hand side of an equality test
        results in a TwoAttributeComparison object rather than an
        AttributeValueComparison or anything else that would be wrong.
        """
        s = Store()
        comparison = (A.reftoc == B.storeID)
        self.assertEquals(
            comparison.getQuery(s),
            '(%s.[reftoc] = %s.oid)' % (
                A.getTableName(s),
                B.getTableName(s)))
        self.assertEquals(comparison.getArgs(s), [])


    def test_leftHandStoreIDComparison(self):
        """
        Test that a StoreID column on the left-hand side of an equality test
        results in a TwoAttributeComparison object rather than an
        AttributeValueComparison or anything else that would be wrong.
        """
        s = Store()
        comparison = (B.storeID == A.reftoc)
        self.assertEquals(
            comparison.getQuery(s),
            '(%s.oid = %s.[reftoc])' % (
                B.getTableName(s),
                A.getTableName(s)))
        self.assertEquals(comparison.getArgs(s), [])


    def test_simplestQuery(self):
        """
        Test that an ItemQuery with no comparison, sorting, or limit generates
        the right SQL for that operation.
        """
        s = Store()
        query = ItemQuery(s, A)
        sql, args = query._sqlAndArgs('SELECT', '*')
        self.assertEquals(
            sql,
            'SELECT * FROM %s' % (A.getTableName(s),))
        self.assertEquals(args, [])


    def test_simpleIntegerComparison(self):
        """
        Test that an ItemQuery with a single attribute comparison on an integer
        attribute generates SQL with the right WHERE clause.
        """
        s = Store()
        query = ItemQuery(s, E, E.amount == 0)
        sql, args = query._sqlAndArgs('SELECT', '*')
        self.assertEquals(
            sql,
            'SELECT * FROM %s WHERE (%s.[amount] = ?)' % (
                E.getTableName(s),
                E.getTableName(s)))
        self.assertEquals(args, [0])


    def test_simpleReferenceComparison(self):
        """
        Test that an ItemQuery with a single attribute comparison on a
        reference attribute generates SQL with the right WHERE clause.
        """
        s = Store()
        query = ItemQuery(s, A, A.reftoc == A.storeID)
        sql, args = query._sqlAndArgs('SELECT', '*')
        self.assertEquals(
            sql,
            'SELECT * FROM %s WHERE (%s.[reftoc] = %s.oid)' % (
                A.getTableName(s),
                A.getTableName(s),
                A.getTableName(s)))
        self.assertEquals(args, [])


    def test_reversedReferenceComparison(self):
        """
        Test that an ItemQuery with a single attribute comparison on a
        reference attribute with the storeID part on the left-hand side
        generates SQL with the right WHERE clause.
        """
        s = Store()
        query = ItemQuery(s, A, A.storeID == A.reftoc)
        sql, args = query._sqlAndArgs('SELECT', '*')
        self.assertEquals(
            sql,
            'SELECT * FROM %s WHERE (%s.oid = %s.[reftoc])' % (
                A.getTableName(s),
                A.getTableName(s),
                A.getTableName(s)))
        self.assertEquals(args, [])


    def test_unionComparison(self):
        """
        Test that an ItemQuery with two comparisons joined with an L{AND}
        generates the right WHERE clause.
        """
        s = Store()
        query = ItemQuery(s, A, AND(A.reftoc == B.storeID,
                                    B.cref == C.storeID))
        sql, args = query._sqlAndArgs('SELECT', '*')
        self.assertEquals(
            sql,
            'SELECT * FROM %s, %s, %s '
            'WHERE ((%s.[reftoc] = %s.oid) AND '
                   '(%s.[cref] = %s.oid))' % (
                A.getTableName(s),
                B.getTableName(s),
                C.getTableName(s),
                A.getTableName(s),
                B.getTableName(s),
                B.getTableName(s),
                C.getTableName(s)))
        self.assertEquals(args, [])


    def testBasicQuery(self):
        s = Store()

        def entesten():
            c1 = C(store=s,
                   name=u'yes')

            c2 = C(store=s,
                   name=u'no')

            A(store=s,
              reftoc=c1,
              type=u'testc')

            A(store=s,
              reftoc=c2,
              type=u'testc')

            A(store=s,
              reftoc=c1,
              type=u'testx')

            yesb = B(store=s,
                     cref=c1,
                     name=u'correct')

            B(store=s,
              cref=c2,
              name=u'not correct')

            s.checkpoint()

            q = list(s.query(B,
                             AND(AND(C.name == u'yes',
                                     A.type == u'testc'),
                                 AND(C.storeID == B.cref,
                                     A.reftoc == C.storeID)),
                             ))

            self.assertEquals(q, [yesb])

        s.transact(entesten)
        s.close()


    def testStringQueries(self):
        s = Store()

        def createAndStuff():
            text1 = u'Hello, \u1234 world.'
            text2 = u'ThIs sTrInG iS nOt cAsE sEnSiTIvE.  \u4567'
            bytes1 = '\x00, punk'

            x = ThingWithCharacterAndByteStrings(
                store=s,
                characterString=text1,
                caseInsensitiveCharString=text2,
                byteString=bytes1)

            x.checkpoint()

            q = list(
                s.query(ThingWithCharacterAndByteStrings,
                        ThingWithCharacterAndByteStrings.characterString == text1.lower(),
                        ))
            self.failIf(q, q)

            q = list(
                s.query(ThingWithCharacterAndByteStrings,
                        ThingWithCharacterAndByteStrings.characterString == text1.upper(),
                        ))
            self.failIf(q, q)

            q = list(
                s.query(ThingWithCharacterAndByteStrings,
                        ThingWithCharacterAndByteStrings.characterString == text1,
                        ))

            self.assertEquals(q, [x])

            q = list(
                s.query(ThingWithCharacterAndByteStrings,
                        ThingWithCharacterAndByteStrings.caseInsensitiveCharString == text2,
                        ))

            self.assertEquals(q, [x])

            q = list(
                s.query(ThingWithCharacterAndByteStrings,
                        ThingWithCharacterAndByteStrings.caseInsensitiveCharString == text2.lower(),
                        ))

            self.assertEquals(q, [x])

            q = list(
                s.query(ThingWithCharacterAndByteStrings,
                        ThingWithCharacterAndByteStrings.caseInsensitiveCharString == text2.upper(),
                        ))

            self.assertEquals(q, [x])

            q = list(
                s.query(ThingWithCharacterAndByteStrings,
                        ThingWithCharacterAndByteStrings.byteString == bytes1,
                        ))

            self.assertEquals(q, [x])

            q = list(
                s.query(ThingWithCharacterAndByteStrings,
                        ThingWithCharacterAndByteStrings.byteString == bytes1.upper(),
                        ))

            self.failIf(q, q)

        s.transact(createAndStuff)
        s.close()


    def testAggregateQueries(self):
        s = Store()
        def entesten():
            self.assertEquals(s.query(E).count(), 0)
            self.assertEquals(s.query(E).getColumn("amount").sum(), 0)

            e1 = E(store=s, name=u'widgets', amount=37)
            e2 = E(store=s, name=u'widgets', amount=63)
            e3 = E(store=s, name=u'quatloos', amount=99, transaction=u'yes')
            s.checkpoint()
            q = s.count(E, E.name == u'widgets')
            self.failUnlessEqual(q, 2)
            q = s.sum(E.amount, E.name == u'widgets')
            self.failUnlessEqual(q, 100)
        s.transact(entesten)
        s.close()

    def testAttributeQueries(self):
        s = Store()
        def entesten():
            E(store=s, name=u'b', amount=456)
            E(store=s, name=u'a', amount=123)
            E(store=s, name=u'c', amount=789)
            self.assertEquals(list(s.query(E, sort=E.name.ascending).getColumn("amount")),
                              [123, 456, 789])

        s.transact(entesten)
        s.close()

    def testAttributeQueryCount(self):
        s = Store()
        def entesten():
            E(store=s, name=u'a', amount=123)
            E(store=s, name=u'b', amount=456)
            E(store=s, name=u'c')  # no amount given
            self.assertEquals(s.query(E).getColumn("amount").count(), 2)
        s.transact(entesten)
        s.close()

    def testAttributeQueryDistinct(self):
        s = Store()
        def entesten():
            E(store=s, name=u'a', amount=123)
            E(store=s, name=u'b', amount=789)
            E(store=s, name=u'a', amount=456)
            self.assertEquals(list(s.query(E, sort=E.name.ascending).getColumn("name").distinct()),
                              [u"a", u"b"])
        s.transact(entesten)
        s.close()

    def testAttributeQueryMinMax(self):
        s = Store()
        def entesten():
            E(store=s, amount=-4)
            E(store=s, amount=10)
            E(store=s, amount=99)
            E(store=s, amount=456)

            self.assertEquals(s.query(E).getColumn("amount").min(), -4)
            self.assertEquals(s.query(E).getColumn("amount").max(), 456)

            self.assertRaises(ValueError, s.query(D).getColumn("id").max)
            self.assertRaises(ValueError, s.query(D).getColumn("id").min)

            self.assertEquals(s.query(D).getColumn("id").min(default=41), 41)
            self.assertEquals(s.query(D).getColumn("id").max(default=42), 42)


        s.transact(entesten)
        s.close()

class QueryingTestCase(TestCase):
    def setUp(self):
        s = self.store = Store()
        def _createStuff():
            self.d1 = D(store=s, one='d1.one', two='d1.two', three='d1.three', four=u'd1.four', id='1')
            self.d2 = D(store=s, one='d2.one', two='d2.two', three='d2.three', four=u'd2.four', id='2')
            self.d3 = D(store=s, one='d3.one', two='d3.two', three='d3.three', four=u'd3.four', id='3')
        s.transact(_createStuff)

    def tearDown(self):
        self.store.close()

    def query(self, *a, **kw):
        return list(self.store.query(*a, **kw))

    def assertQuery(self, query, expected, args=None):
        """
        Perform byte-for-byte comparisons against generated SQL.  It would be
        slightly nicer if we have a SQL parser which emited an AST we could
        test against instead, but in the absence of that, we'll do the more
        difficult thing and keep the tests in sync with the SQL generator.
        If, someday, we have multiple backends which have different SQL
        generation requirements, we'll probably need to split all these tests
        up.

        While it is true that we don't actually directly care about what SQL
        gets generated, we do want to test the SQL generation as a /unit/,
        rather than indirectly testing it by making assertions about the
        result set it generates.  This for all the usual reasons one writes
        unit tests (ease of debugging, refactoring, maintenance).  Other
        tests cover the actual query behavior this SQL results in, and
        ideally some day we will have some tests which interact with the
        actual underlying rdbm to test basic assumptions we are making about
        the behavior of particular snippets of SQL.

        To sum up, changes to the SQL generation code may rightly require
        changes to tests which use assertQuery.  If the SQL we want to generate
        changes, do not be afraid to update the tests.
        """
        if args is None:
            args = []

        sql = query.getQuery(self.store)
        self.assertEquals(
            sql,
            expected,
            "\n%r != %r\n(if SQL generation code has changed, maybe this test "
            "should be updated)\n" % (sql, expected))
        self.assertEquals([str(a) for a in query.getArgs(self.store)], args)


class AndOrQueries(QueryingTestCase):
    def testNoConditions(self):
        self.assertRaises(ValueError, AND)
        self.assertRaises(ValueError, OR)

    def testOneCondition(self):
        self.assertQuery(
            AND(A.type == u'Narf!'),
            '((%s = ?))' % (A.type.getColumnName(self.store),),
            ['Narf!'])
        self.assertQuery(
            OR(A.type == u'Narf!'),
            '((%s = ?))' % (A.type.getColumnName(self.store),),
            ['Narf!'])
        self.assertEquals(self.query(D, AND(D.one == 'd1.one')), [self.d1])
        self.assertEquals(self.query(D, OR(D.one == 'd1.one')), [self.d1])

    def testMultipleAndConditions(self):
        condition = AND(A.type == u'Narf!',
                        A.type == u'Poiuyt!',
                        A.type == u'Try to take over the world')

        expectedSQL = '((%s = ?) AND (%s = ?) AND (%s = ?))'
        expectedSQL %= (A.type.getColumnName(self.store),) * 3

        self.assertQuery(
            condition,
            expectedSQL,
            ['Narf!', 'Poiuyt!', 'Try to take over the world'])
        self.assertEquals(
            self.query(D, AND(D.one == 'd1.one',
                              D.two == 'd1.two',
                              D.three == 'd1.three')),
            [self.d1])

    def testMultipleOrConditions(self):
        condition = OR(A.type == u'Narf!',
                       A.type == u'Poiuyt!',
                       A.type == u'Try to take over the world')
        expectedSQL = '((%s = ?) OR (%s = ?) OR (%s = ?))'
        expectedSQL %= (A.type.getColumnName(self.store),) * 3
        self.assertQuery(
            condition,
            expectedSQL,
            ['Narf!', 'Poiuyt!', 'Try to take over the world'])
        q = self.query(D, OR(D.one == 'd1.one',
                             D.one == 'd2.one',
                             D.one == 'd3.one'))
        e = [self.d1, self.d2, self.d3]
        self.assertEquals(sorted(q), sorted(e))


class SetMembershipQuery(QueryingTestCase):

    def test_oneOfValueQueryGeneration(self):
        """
        Test that comparing an attribute for containment against a value set
        generates the appropriate SQL.
        """
        values = [u'a', u'b', u'c']
        comparison = C.name.oneOf(values)
        self.failUnless(IComparison.providedBy(comparison))
        self.assertEquals(
            comparison.getQuery(self.store),
            '%s IN (?, ?, ?)' % (
                C.name.getColumnName(self.store),))
        self.assertEquals(
            comparison.getArgs(self.store),
            values)


    def test_oneOfColumnQueryGeneration(self):
        """
        Test that comparing an attribute for containment against an L{IColumn}
        generates the appropriate SQL.
        """
        values = A.type
        comparison = C.name.oneOf(values)
        self.failUnless(IComparison.providedBy(comparison))
        self.assertEquals(
            comparison.getQuery(self.store),
            '%s IN (%s)' % (
                C.name.getColumnName(self.store),
                A.type.getColumnName(self.store)))
        self.assertEquals(
            comparison.getArgs(self.store),
            [])


    def test_oneOfColumnQueryQueryGeneration(self):
        """
        Test that comparing an attribute for containment against another query
        generates a sub-select.
        """
        subselect = self.store.query(A).getColumn('type')
        comparison = C.name.oneOf(subselect)
        self.failUnless(IComparison.providedBy(comparison))
        self.assertEquals(
            comparison.getQuery(self.store),
            '%s IN (SELECT %s FROM %s)' % (
                C.name.getColumnName(self.store),
                A.type.getColumnName(self.store),
                A.getTableName(self.store)))
        self.assertEquals(
            comparison.getArgs(self.store),
            [])


    def test_oneOfColumnQueryQueryGenerationWithArguments(self):
        """
        Like test_oneOfColumnQueryQueryGeneration, but pass some values to the
        subselect and make sure they come out of the C{getArgs} method
        properly.
        """
        value = '10'
        subselect = self.store.query(
            D,
            AND(D.id == value,
                D.four == C.name)).getColumn('one')

        comparison = C.name.oneOf(subselect)
        self.failUnless(IComparison.providedBy(comparison))
        self.assertEquals(
            comparison.getQuery(self.store),
            '%s IN (SELECT %s FROM %s, %s WHERE ((%s = ?) AND (%s = %s)))' % (
                C.name.getColumnName(self.store),
                D.one.getColumnName(self.store),
                C.getTableName(self.store),
                D.getTableName(self.store),
                D.id.getColumnName(self.store),
                D.four.getColumnName(self.store),
                C.name.getColumnName(self.store)))
        self.assertEquals(
            map(str, comparison.getArgs(self.store)),
            [value])


    def testOneOfWithList(self):
        cx = C(store=self.store, name=u'x')
        cy = C(store=self.store, name=u'y')
        cz = C(store=self.store, name=u'z')

        query = self.store.query(
            C, C.name.oneOf([u'x', u'z', u'a']), sort=C.name.ascending)

        self.assertEquals(list(query), [cx, cz])


    def testOneOfWithSet(self):
        s = Store()

        cx = C(store=s, name=u'x')
        cy = C(store=s, name=u'y')
        cz = C(store=s, name=u'z')

        self.assertEquals(list(s.query(C, C.name.oneOf(set([u'x', u'z', u'a'])), sort=C.name.ascending)),
                          [cx, cz])


class WildcardQueries(QueryingTestCase):
    def testNoConditions(self):
        self.assertRaises(TypeError, D.one.like)
        self.assertRaises(TypeError, D.one.notLike)

    def testOneString(self):
        self.assertQuery(
            D.one.like('foobar%'),
            '(%s LIKE (?))' % (D.one.getColumnName(self.store),),
            ['foobar%'])
        self.assertQuery(
            D.one.notLike('foobar%'),
            '(%s NOT LIKE (?))' % (D.one.getColumnName(self.store),),
            ['foobar%'])
        self.assertEquals(self.query(D, D.one.like('d1.one')), [self.d1])
        self.assertEquals(self.query(D, D.one.notLike('d%.one')), [])

    def testOneColumn(self):
        self.assertQuery(
            D.one.like(D.two),
            '(%s LIKE (%s))' % (D.one.getColumnName(self.store),
                                D.two.getColumnName(self.store)))
        self.assertEquals(self.query(D, D.one.like(D.two)), [])

    def testOneColumnAndStrings(self):
        self.assertQuery(
            D.one.like('%', D.id, '%one'),
            '(%s LIKE (? || %s || ?))' % (D.one.getColumnName(self.store),
                                          D.id.getColumnName(self.store)),
            ['%', '%one'])
        q = self.query(D, D.one.like('%', D.id, '%one'))
        e = [self.d1, self.d2, self.d3]
        self.assertEquals(sorted(q), sorted(e))

    def testMultipleColumns(self):
        self.assertQuery(
            D.one.like(D.two, '%', D.three),
            '(%s LIKE (%s || ? || %s))' % (D.one.getColumnName(self.store),
                                           D.two.getColumnName(self.store),
                                           D.three.getColumnName(self.store)),
            ['%'])
        self.assertEquals(
            self.query(D, D.one.like(D.two, '%', D.three)), [])


    def testStartsEndsWith(self):
        self.assertQuery(
            D.one.startswith('foo'),
            '(%s LIKE (?))' % (D.one.getColumnName(self.store),),
            ['foo%'])
        self.assertQuery(
            D.one.endswith('foo'),
            '(%s LIKE (?))' % (D.one.getColumnName(self.store),),
            ['%foo'])
        self.assertEquals(
            self.query(D, D.one.startswith('d1')), [self.d1])
        self.assertEquals(
            self.query(D, D.one.endswith('3.one')), [self.d3])


    def testStartsEndsWithColumn(self):
        self.assertQuery(
            D.one.startswith(D.two),
            '(%s LIKE (%s || ?))' % (D.one.getColumnName(self.store),
                                     D.two.getColumnName(self.store)),
            ['%'])
        self.assertEquals(
            self.query(D, D.one.startswith(D.two)), [])


    def testStartsEndsWithText(self):
        self.assertEquals(
            self.query(D, D.four.startswith(u'd1')),
            [self.d1])
        self.assertEquals(
            self.query(D, D.four.endswith(u'2.four')),
            [self.d2])


    def testOtherTable(self):
        self.assertQuery(
            D.one.startswith(A.type),
            '(%s LIKE (%s || ?))' % (D.one.getColumnName(self.store),
                                     A.type.getColumnName(self.store)),
            ['%'])

        C(store=self.store, name=u'd1.')
        C(store=self.store, name=u'2.one')
        self.assertEquals(
            self.query(D, D.one.startswith(C.name)), [self.d1])
        self.assertEquals(
            self.query(D, D.one.endswith(C.name)), [self.d2])


class UniqueTest(TestCase):

    def setUp(self):
        s = self.s = Store()
        self.c = C(store=s, name=u'unique')
        self.dupc1 = C(store=s, name=u'non-unique')
        self.dupc2 = C(store=s, name=u'non-unique')

    def testUniqueFound(self):
        self.assertEquals(self.s.findUnique(C, C.name == u'unique'), self.c)

    def testUniqueNotFoundError(self):
        self.assertRaises(errors.ItemNotFound, self.s.findUnique,
                          C, C.name == u'non-existent')

    def testUniqueNotFoundDefault(self):
        bing = object()
        self.assertEquals(bing, self.s.findUnique(
                C, C.name == u'non-existent',
                default=bing))

    def testUniqueDuplicate(self):
        self.assertRaises(errors.DuplicateUniqueItem,
                          self.s.findUnique, C, C.name == u'non-unique')



class PlaceholderTestItem(Item):
    """
    Type used by the placeholder support test cases.
    """
    attr = integer()
    other = integer()
    characters = text()


COMPARISON_OPS = [
    operator.lt, operator.le, operator.eq,
    operator.ne, operator.ge, operator.gt]

class PlaceholderTestCase(TestCase):
    """
    Tests for placeholder table name support.
    """
    def test_placeholderType(self):
        """
        Test that the C{type} attribute of a Placeholder column is the
        Placeholder from which it came.
        """
        p = Placeholder(PlaceholderTestItem)
        a = p.attr
        self.assertIdentical(a.type, p)


    def test_placeholderTableName(self):
        """
        Test that the table name of a Placeholder is the same as the table name
        of the underlying Item class.
        """
        s = Store()
        p = Placeholder(PlaceholderTestItem)
        self.assertEquals(p.getTableName(s), PlaceholderTestItem.getTableName(s))


    def test_placeholderColumnInterface(self):
        """
        Test that a column from a placeholder provides L{IColumn}.
        """
        value = 0
        p = Placeholder(PlaceholderTestItem)
        a = p.attr
        self.failUnless(IColumn.providedBy(a))


    def test_placeholderAttributeValueComparison(self):
        """
        Test that getting an attribute from a Placeholder which exists on the
        underlying Item class and comparing it to a value returns an
        L{IComparison} provider.
        """
        value = 0
        p = Placeholder(PlaceholderTestItem)
        for op in COMPARISON_OPS:
            self.failUnless(IComparison.providedBy(op(p.attr, value)))
            self.failUnless(IComparison.providedBy(op(value, p.attr)))


    def test_placeholderAttributeColumnComparison(self):
        """
        Test that getting an attribute from a Placeholder which exists on the
        underlying Item class and comparing it to another column returns an
        L{IComparison} provider.
        """
        value = 0
        p = Placeholder(PlaceholderTestItem)
        for op in COMPARISON_OPS:
            self.failUnless(IComparison.providedBy(op(p.attr, PlaceholderTestItem.attr)))
            self.failUnless(IComparison.providedBy(op(PlaceholderTestItem.attr, p.attr)))


    def _placeholderAttributeSimilarity(self, kind, sql, args):
        s = Store()
        value = u'text'

        p = Placeholder(PlaceholderTestItem)

        # Explicitly call this, since we aren't going through ItemQuery.
        p.getTableAlias(s, ())

        comparison = getattr(p.characters, kind)(value)
        self.failUnless(IComparison.providedBy(comparison))
        self.assertEquals(comparison.getQuery(s),
                          sql % (p.characters.getColumnName(s),))
        self.assertEquals(
            comparison.getArgs(s),
            [args % (value,)])


    def test_placeholderAttributeSimilarity(self):
        """
        Test that placeholder attributes can be used with the SQL LIKE
        operator.
        """
        return self._placeholderAttributeSimilarity('like', '(%s LIKE (?))', '%s')


    def test_placeholderAttributeDisimilarity(self):
        """
        Test that placeholder attributes can be used with the SQL NOT LIKE
        operator.
        """
        return self._placeholderAttributeSimilarity('notLike', '(%s NOT LIKE (?))', '%s')


    def test_placeholderAttributeStartsWith(self):
        """
        Test that placeholder attributes work with the .startswith() method.
        """
        return self._placeholderAttributeSimilarity('startswith', '(%s LIKE (?))', '%s%%')


    def test_placeholderAttributeEndsWith(self):
        """
        Test that placeholder attributes work with the .endswith() method.
        """
        return self._placeholderAttributeSimilarity('endswith', '(%s LIKE (?))', '%%%s')


    def test_placeholderLikeTarget(self):
        """
        Test that a placeholder can be used as the right-hand argument to a SQL
        LIKE expression.
        """
        s = Store()
        p = Placeholder(PlaceholderTestItem)

        # Call this since we're not using ItemQuery
        p.getTableAlias(s, ())

        comparison = PlaceholderTestItem.attr.like(p.attr)
        self.failUnless(IComparison.providedBy(comparison))
        self.assertEquals(
            comparison.getQuery(s),
            '(%s LIKE (placeholder_0.[attr]))' % (
                PlaceholderTestItem.attr.getColumnName(s),))
        self.assertEquals(
            comparison.getArgs(s),
            [])


    def test_placeholderContainment(self):
        """
        Test that placeholder attributes can be used with the SQL IN and NOT IN
        operators.
        """
        s = Store()
        value = [1, 2, 3]
        p = Placeholder(PlaceholderTestItem)

        # Call this since we're not using ItemQuery
        p.getTableAlias(s, ())

        comparison = p.attr.oneOf(value)
        self.failUnless(IComparison.providedBy(comparison))
        self.assertEquals(
            comparison.getQuery(s),
            '%s IN (?, ?, ?)' % (p.attr.getColumnName(s),))
        self.assertEquals(
            comparison.getArgs(s),
            value)


    def test_placeholderAntiContainment(self):
        """
        Test that placeholder attributes can be used with the SQL NOT IN
        operator.
        """
        s = Store()
        value = [1, 2, 3]
        p = Placeholder(PlaceholderTestItem)

        # Call this since we're not using ItemQuery
        p.getTableAlias(s, ())

        comparison = p.attr.notOneOf(value)
        self.failUnless(IComparison.providedBy(comparison))
        self.assertEquals(
            comparison.getQuery(s),
            '%s NOT IN (?, ?, ?)' % (p.attr.getColumnName(s),))
        self.assertEquals(
            comparison.getArgs(s),
            value)


    def test_placeholderContainmentTarget(self):
        """
        Test that a placeholder attribute can be used as the right-hand
        argument to the SQL IN operator.
        """
        s = Store()
        p = Placeholder(PlaceholderTestItem)

        # Call this since we're not using ItemQuery
        p.getTableAlias(s, ())

        comparison = PlaceholderTestItem.attr.oneOf(p.attr)
        self.failUnless(IComparison.providedBy(comparison))
        self.assertEquals(
            comparison.getQuery(s),
            '%s IN (%s)' % (PlaceholderTestItem.attr.getColumnName(s),
                            p.attr.getColumnName(s)))
        self.assertEquals(
            comparison.getArgs(s),
            [])


    def test_placeholderAntiContainmentTarget(self):
        """
        Test that a placeholder attribute can be used as the right-hand
        argument to the SQL NOT IN operator.
        """
        s = Store()
        p = Placeholder(PlaceholderTestItem)

        # Call this since we're not using ItemQuery
        p.getTableAlias(s, ())

        comparison = PlaceholderTestItem.attr.notOneOf(p.attr)
        self.failUnless(IComparison.providedBy(comparison))
        self.assertEquals(
            comparison.getQuery(s),
            '%s NOT IN (%s)' % (PlaceholderTestItem.attr.getColumnName(s),
                            p.attr.getColumnName(s)))
        self.assertEquals(
            comparison.getArgs(s),
            [])


    def test_placeholderStoreID(self):
        """
        Test that the C{storeID} attribute of a Placeholder can be retrieved
        just like any other attribute.
        """
        value = 0
        p = Placeholder(PlaceholderTestItem)
        self.failUnless(IComparison.providedBy(p.storeID > value))


    def test_placeholderAttributeError(self):
        """
        Test that trying to get an attribute from a Placeholder which is not an
        L{IComparison} on the underlying Item class raises an AttributeError.
        """
        p = Placeholder(PlaceholderTestItem)
        self.assertRaises(AttributeError, getattr, p, 'nonexistentAttribute')


    def test_placeholderComparisonTables(self):
        """
        Test that the result of L{IComparison.getInvolvedTables} on an
        attribute retrieved from a Placeholder returns a special placeholder
        item.
        """
        s = Store()
        p = Placeholder(PlaceholderTestItem)
        value = 0
        involvedTables = (p.attr > value).getInvolvedTables()
        self.assertEquals(len(involvedTables), 1)
        theTable = iter(involvedTables).next()
        self.assertEquals(theTable.getTableName(s),
                          PlaceholderTestItem.getTableName(s))
        self.assertEquals(theTable.getTableAlias(s, ()),
                          'placeholder_0')


    def test_placeholderComparisonQuery(self):
        """
        Test that the result of L{IComparison.getQuery} on an attribute
        retrieved from a Placeholder returns SQL which correctly uses an alias
        of the wrapped table.
        """
        s = Store()
        p = Placeholder(PlaceholderTestItem)

        # Explicitly call this here, since we're not going through ItemQuery or
        # another more reasonable codepath, which would have called it for us.
        p.getTableAlias(s, ())

        value = 0
        comparison = (p.attr > value)
        self.assertEquals(
            comparison.getQuery(s),
            '(placeholder_0.[attr] > ?)')
        self.assertEquals(
            comparison.getArgs(s),
            [value])


    def test_placeholderComparisonArgs(self):
        """
        Test that the result of L{IComparison.getArgs} on an attribute
        retrieved from a Placeholder returns the right values for the
        comparison.
        """
        s = Store()
        p = Placeholder(PlaceholderTestItem)
        value = 0
        args = (p.attr > value).getArgs(s)
        self.assertEquals(args, [0])


    def test_placeholderQuery(self):
        """
        Test that a BaseQuery can be created with Placeholder instances and the
        SQL it emits as a result correctly assigns and uses table aliases.
        """
        s = Store()
        p = Placeholder(PlaceholderTestItem)
        sql, args = ItemQuery(s, p)._sqlAndArgs('SELECT', '*')
        self.assertEquals(
            sql,
            'SELECT * FROM %s AS placeholder_0' % (
                PlaceholderTestItem.getTableName(s),))


    def test_placeholderComparison(self):
        """
        Test that a comparison which contains a Placeholder also results in
        properly generated SQL.
        """
        s = Store()
        p = Placeholder(PlaceholderTestItem)
        query = ItemQuery(
            s,
            PlaceholderTestItem,
            PlaceholderTestItem.attr == p.attr)
        sql, args = query._sqlAndArgs('SELECT', '*')
        self.assertEquals(
            sql,
            'SELECT * '
            'FROM %s, %s AS placeholder_0 '
            'WHERE (%s.[attr] = placeholder_0.[attr])' % (
                PlaceholderTestItem.getTableName(s),
                PlaceholderTestItem.getTableName(s),
                PlaceholderTestItem.getTableName(s)))
        self.assertEquals(args, [])


    def test_placeholderOrdering(self):
        """
        Placeholders should be ordered based on the order in which they were
        instantiated.
        """
        p1 = Placeholder(PlaceholderTestItem)
        p2 = Placeholder(PlaceholderTestItem)
        self.failUnless(p1 < p2)
        self.failUnless(p2 > p1)
        self.failIf(p1 >= p2)
        self.failIf(p2 <= p1)
        self.failIf(p1 == p2)
        self.failIf(p2 == p1)
        self.failUnless(p1 != p2)
        self.failUnless(p2 != p1)


    def test_placeholderSorting(self):
        """
        Placeholders should sort based on the order in which they were
        instantiated.
        """
        placeholders = [Placeholder(PlaceholderTestItem) for n in xrange(10)]
        shuffledPlaceholders = list(placeholders)
        random.shuffle(shuffledPlaceholders)
        shuffledPlaceholders.sort()
        self.assertEquals(placeholders, shuffledPlaceholders)


    def test_placeholderAliasAssignment(self):
        """
        Test that each placeholder selects a unique alias for itself.
        """
        s = Store()
        p1 = Placeholder(PlaceholderTestItem)
        p2 = Placeholder(PlaceholderTestItem)

        aliases = []
        self.assertEquals(p1.getTableAlias(s, aliases), 'placeholder_0')
        self.assertEquals(p1.getTableAlias(s, aliases), 'placeholder_0')
        aliases.append('placeholder_')
        self.assertEquals(p1.getTableAlias(s, aliases), 'placeholder_0')
        self.assertEquals(p2.getTableAlias(s, aliases), 'placeholder_1')


    def test_multiplePlaceholderComparisons(self):
        """
        Test that using multiple different placeholders in a comparison at once
        properly gives each a unique name.
        """
        s = Store()
        p1 = Placeholder(PlaceholderTestItem)
        p2 = Placeholder(PlaceholderTestItem)

        query = ItemQuery(
            s,
            PlaceholderTestItem,
            AND(PlaceholderTestItem.attr == p1.attr,
                PlaceholderTestItem.other == p1.other,
                PlaceholderTestItem.attr == p2.attr,
                PlaceholderTestItem.characters == p2.characters))
        sql, args = query._sqlAndArgs('SELECT', '*')
        self.assertEquals(
            sql,
            'SELECT * '
            'FROM %s, %s AS placeholder_0, %s AS placeholder_1 '
            'WHERE ((%s = placeholder_0.[attr]) AND '
                   '(%s = placeholder_0.[other]) AND '
                   '(%s = placeholder_1.[attr]) AND '
                   '(%s = placeholder_1.[characters]))' % (
                PlaceholderTestItem.getTableName(s),
                PlaceholderTestItem.getTableName(s),
                PlaceholderTestItem.getTableName(s),
                PlaceholderTestItem.attr.getColumnName(s),
                PlaceholderTestItem.other.getColumnName(s),
                PlaceholderTestItem.attr.getColumnName(s),
                PlaceholderTestItem.characters.getColumnName(s)))
        self.assertEquals(args, [])


    def test_placeholderSorting(self):
        """
        Test that a placeholder attribute can be used as a sort key.
        """
        s = Store()
        p = Placeholder(PlaceholderTestItem)

        query = ItemQuery(
            s,
            PlaceholderTestItem,
            sort=p.attr.ascending)
        sql, args = query._sqlAndArgs('SELECT', '*')

        expectedSQL = ('SELECT * '
                       'FROM %s, %s AS placeholder_0 '
                       'ORDER BY placeholder_0.[attr] ASC')
        expectedSQL %= (PlaceholderTestItem.getTableName(s),) * 2

        self.assertEquals(sql, expectedSQL)
        self.assertEquals(args, [])
