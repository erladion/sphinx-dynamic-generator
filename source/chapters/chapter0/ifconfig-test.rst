.. metadata::
   :content_order: 20
   :content_title: Testing config 

Ifconfig Testing Document
=========================

.. ifconfig:: should_include

   Condition should_include
   ========================

   Should include is now set to true
   Random text to see if the should_include variable works


.. ifconfig:: not should_include

   Condition not should_include
   ============================

   Should-include is now set to false


.. ifconfig:: (should_include and production_build)

   Condition should_include and production_build
   =============================================

   Should_include is set and so is production_build

.. ifconfig:: 'BUILD_TYPE' in env and env['BUILD_TYPE'] == 'production'

   This content is only included if the shell variable BUILD_TYPE is set to 'production'.
   
   Production Instructions
   =======================