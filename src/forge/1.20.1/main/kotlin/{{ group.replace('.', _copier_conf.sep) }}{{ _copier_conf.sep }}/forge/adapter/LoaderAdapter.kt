package {{group}}.forge.adapter

import com.mojang.blaze3d.platform.InputConstants
import net.minecraft.client.KeyMapping
import net.minecraft.client.gui.screens.Screen
import net.minecraft.resources.ResourceKey
import net.minecraft.world.entity.EquipmentSlot
import net.minecraft.world.entity.LivingEntity
import net.minecraft.world.entity.player.Player
import net.minecraft.world.inventory.ClickAction
import net.minecraft.world.inventory.Slot
import net.minecraft.world.item.CreativeModeTab
import net.minecraft.world.item.Item
import net.minecraft.world.item.ItemStack
import net.minecraftforge.client.event.ScreenEvent
import net.minecraftforge.common.MinecraftForge
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent
import net.minecraftforge.event.ItemStackedOnOtherEvent
import net.minecraftforge.event.entity.living.LivingEquipmentChangeEvent
import net.minecraftforge.event.entity.living.LivingEvent.LivingTickEvent
import net.minecraftforge.fml.loading.FMLLoader
import net.minecraftforge.fml.loading.LoadingModList
import {{group}}.adapter.LoaderAdapter
import thedarkcolour.kotlinforforge.forge.MOD_BUS

class LoaderAdapter : LoaderAdapter {
    override val isClient: Boolean
        get() = FMLLoader.getDist().isClient

    override fun isModLoaded(modId: String) = LoadingModList.get().getModFileById(modId) != null

    override fun <T : Item> T.creativeTab(key: ResourceKey<CreativeModeTab>) {
        MOD_BUS.addListener<BuildCreativeModeTabContentsEvent> { event ->
            if (event.tabKey == key) event.accept(this)
        }
    }

    override fun onKeyPressedInScreen(key: KeyMapping, callback: (screen: Screen) -> Unit) {
        MinecraftForge.EVENT_BUS.addListener<ScreenEvent.KeyPressed> { event ->
            if (key.isActiveAndMatches(InputConstants.getKey(event.keyCode, event.scanCode))) {
                callback(event.screen)
            }
        }
    }

    override fun onLivingEntityTick(callback: (entity: LivingEntity) -> Unit) {
        MinecraftForge.EVENT_BUS.addListener<LivingTickEvent> { event ->
            callback(event.entity)
        }
    }

    override fun onEquipmentChanged(callback: (entity: LivingEntity, slot: EquipmentSlot, from: ItemStack, to: ItemStack) -> Unit) {
        MinecraftForge.EVENT_BUS.addListener<LivingEquipmentChangeEvent> { event ->
            callback(event.entity, event.slot, event.from, event.to)
        }
    }

    override fun onItemStackedOnOther(callback: (player: Player, carried: ItemStack, target: ItemStack, slot: Slot, clickAction: ClickAction) -> Boolean) {
        MinecraftForge.EVENT_BUS.addListener<ItemStackedOnOtherEvent> { event ->
            if (callback(event.player, event.carriedItem, event.stackedOnItem, event.slot, event.clickAction)) {
                event.isCanceled = true
            }
        }
    }
}